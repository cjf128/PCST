from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


class MobileSAMOnnxImage:
    """MobileSAM ONNX predictor with the same prompt API used by the viewer."""

    image_size = 1024
    mask_threshold = 0.0

    def __init__(
        self,
        encoder_path: str | Path,
        decoder_path: str | Path,
        providers: list[str] | None = None,
    ) -> None:
        self.encoder_path = Path(encoder_path)
        self.decoder_path = Path(decoder_path)
        self.providers = providers or ["CPUExecutionProvider"]

        so = ort.SessionOptions()
        so.log_severity_level = 3
        self.encoder = ort.InferenceSession(
            str(self.encoder_path), so, providers=self.providers
        )
        self.decoder = ort.InferenceSession(
            str(self.decoder_path), so, providers=self.providers
        )
        self.encoder_input_name = self.encoder.get_inputs()[0].name
        self.decoder_output_names = [item.name for item in self.decoder.get_outputs()]

        self.image_embeddings: np.ndarray | None = None
        self.original_size: tuple[int, int] | None = None
        self.input_size: tuple[int, int] | None = None
        self.masks: dict[int, np.ndarray] = {}
        self.low_res_logits: dict[int, np.ndarray] = {}
        self.point_coords: dict[int, np.ndarray] = {}
        self.point_labels: dict[int, np.ndarray] = {}
        self.box_coords: dict[int, np.ndarray] = {}

    def set_image(self, image: np.ndarray, image_format: str = "BGR") -> None:
        if image_format not in {"RGB", "BGR"}:
            raise ValueError("image_format must be 'RGB' or 'BGR'.")
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("image must be an HxWx3 uint8 array.")

        if image_format == "BGR":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        self.original_size = (int(image.shape[0]), int(image.shape[1]))
        input_image, self.input_size = self._preprocess_image(image)
        self.image_embeddings = self.encoder.run(
            None, {self.encoder_input_name: input_image}
        )[0]
        self.reset_points()

    def add_point(
        self,
        point_coords: tuple[int, int],
        is_positive: bool,
        label_id: int = 1,
    ) -> dict[int, np.ndarray]:
        point = np.array([point_coords], dtype=np.float32)
        label = np.array([1 if is_positive else 0], dtype=np.float32)

        if label_id in self.point_coords:
            self.point_coords[label_id] = np.concatenate(
                [self.point_coords[label_id], point], axis=0
            )
            self.point_labels[label_id] = np.concatenate(
                [self.point_labels[label_id], label], axis=0
            )
        else:
            self.point_coords[label_id] = point
            self.point_labels[label_id] = label

        return self.decode_mask(label_id)

    def set_box(
        self,
        box_coords: tuple[tuple[int, int], tuple[int, int]],
        label_id: int = 1,
    ) -> dict[int, np.ndarray]:
        self.box_coords[label_id] = np.array(
            [box_coords[0], box_coords[1]], dtype=np.float32
        )
        return self.decode_mask(label_id)

    def remove_point(
        self, point_coords: tuple[int, int], label_id: int = 1
    ) -> dict[int, np.ndarray]:
        if label_id not in self.point_coords:
            return self.masks

        points = self.point_coords[label_id]
        matches = np.where(
            (points[:, 0] == point_coords[0]) & (points[:, 1] == point_coords[1])
        )[0]
        if matches.size == 0:
            return self.masks

        point_index = matches[0]
        self.point_coords[label_id] = np.delete(points, point_index, axis=0)
        self.point_labels[label_id] = np.delete(
            self.point_labels[label_id], point_index, axis=0
        )
        if self.point_coords[label_id].size == 0:
            del self.point_coords[label_id]
            del self.point_labels[label_id]

        return self.decode_mask(label_id)

    def remove_box(self, label_id: int = 1) -> dict[int, np.ndarray]:
        self.box_coords.pop(label_id, None)
        return self.decode_mask(label_id)

    def get_masks(self) -> dict[int, np.ndarray]:
        return self.masks

    def reset_points(self) -> None:
        self.masks = {}
        self.low_res_logits = {}
        self.point_coords = {}
        self.point_labels = {}
        self.box_coords = {}

    def decode_mask(self, label_id: int = 1) -> dict[int, np.ndarray]:
        point_coords = self.point_coords.get(label_id)
        point_labels = self.point_labels.get(label_id)
        box = self.box_coords.get(label_id)

        if point_coords is None and box is None:
            if self.original_size is not None:
                self.masks[label_id] = np.zeros(self.original_size, dtype=np.uint8)
            return self.masks

        masks, _, low_res_masks = self.predict(
            point_coords=point_coords, point_labels=point_labels, box=box
        )
        self.masks[label_id] = masks[0]
        self.low_res_logits[label_id] = low_res_masks
        return self.masks

    def predict(
        self,
        point_coords: np.ndarray | None = None,
        point_labels: np.ndarray | None = None,
        box: np.ndarray | None = None,
        mask_input: np.ndarray | None = None,
        return_logits: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.image_embeddings is None or self.original_size is None:
            raise RuntimeError("Call set_image(...) before predict(...).")

        coords, labels = self._build_prompt(point_coords, point_labels, box)
        onnx_coord = self._apply_coords(coords[None, :, :], self.original_size).astype(
            np.float32
        )
        onnx_label = labels[None, :].astype(np.float32)

        if mask_input is None:
            onnx_mask_input = np.zeros((1, 1, 256, 256), dtype=np.float32)
            has_mask_input = np.zeros((1,), dtype=np.float32)
        else:
            onnx_mask_input = self._normalize_mask_input(mask_input)
            has_mask_input = np.ones((1,), dtype=np.float32)

        inputs = {
            "image_embeddings": self.image_embeddings,
            "point_coords": onnx_coord,
            "point_labels": onnx_label,
            "mask_input": onnx_mask_input,
            "has_mask_input": has_mask_input,
            "orig_im_size": np.array(self.original_size, dtype=np.float32),
        }
        masks, scores, low_res_masks = self.decoder.run(
            self.decoder_output_names, inputs
        )

        masks = masks[0]
        if not return_logits:
            masks = (masks > self.mask_threshold).astype(np.uint8)
        return masks, scores[0], low_res_masks

    def _preprocess_image(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, tuple[int, int]]:
        old_h, old_w = image.shape[:2]
        new_h, new_w = self._get_preprocess_shape(old_h, old_w, self.image_size)

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        resized = resized.astype(np.float32)

        mean = np.array([123.675, 116.28, 103.53], dtype=np.float32)
        std = np.array([58.395, 57.12, 57.375], dtype=np.float32)
        normalized = (resized - mean) / std
        chw = normalized.transpose(2, 0, 1)

        padded = np.zeros((3, self.image_size, self.image_size), dtype=np.float32)
        padded[:, :new_h, :new_w] = chw
        return padded[None, :, :, :], (new_h, new_w)

    def _build_prompt(
        self,
        point_coords: np.ndarray | None,
        point_labels: np.ndarray | None,
        box: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        coords_parts = []
        label_parts = []

        if point_coords is not None:
            if point_labels is None:
                raise ValueError(
                    "point_labels must be supplied when point_coords is supplied."
                )
            point_coords = np.asarray(point_coords, dtype=np.float32).reshape(-1, 2)
            point_labels = np.asarray(point_labels, dtype=np.float32).reshape(-1)
            if point_coords.shape[0] != point_labels.shape[0]:
                raise ValueError(
                    "point_coords and point_labels must have the same length."
                )
            coords_parts.append(point_coords)
            label_parts.append(point_labels)

        if box is not None:
            box_coords = np.asarray(box, dtype=np.float32)
            if box_coords.shape == (4,):
                box_coords = box_coords.reshape(2, 2)
            if box_coords.shape != (2, 2):
                raise ValueError(
                    "box must be [x0, y0, x1, y1] or [[x0, y0], [x1, y1]]."
                )
            coords_parts.append(box_coords)
            label_parts.append(np.array([2, 3], dtype=np.float32))

        if not coords_parts:
            raise ValueError("At least one point or box prompt is required.")

        coords = np.concatenate(coords_parts, axis=0)
        labels = np.concatenate(label_parts, axis=0)
        if box is None:
            coords = np.concatenate(
                [coords, np.array([[0.0, 0.0]], dtype=np.float32)], axis=0
            )
            labels = np.concatenate(
                [labels, np.array([-1.0], dtype=np.float32)], axis=0
            )
        return coords, labels

    def _apply_coords(
        self, coords: np.ndarray, original_size: tuple[int, int]
    ) -> np.ndarray:
        old_h, old_w = original_size
        new_h, new_w = self._get_preprocess_shape(old_h, old_w, self.image_size)
        transformed = coords.copy().astype(np.float32)
        transformed[..., 0] = transformed[..., 0] * (new_w / old_w)
        transformed[..., 1] = transformed[..., 1] * (new_h / old_h)
        return transformed

    @staticmethod
    def _normalize_mask_input(mask_input: np.ndarray) -> np.ndarray:
        mask_input = np.asarray(mask_input, dtype=np.float32)
        if mask_input.shape == (256, 256):
            mask_input = mask_input[None, None, :, :]
        elif mask_input.shape == (1, 256, 256):
            mask_input = mask_input[None, :, :, :]
        elif mask_input.shape != (1, 1, 256, 256):
            raise ValueError(
                "mask_input must have shape 256x256, 1x256x256, or 1x1x256x256."
            )
        return mask_input

    @staticmethod
    def _get_preprocess_shape(
        old_h: int, old_w: int, long_side_length: int
    ) -> tuple[int, int]:
        scale = long_side_length * 1.0 / max(old_h, old_w)
        new_h = int(old_h * scale + 0.5)
        new_w = int(old_w * scale + 0.5)
        return new_h, new_w
