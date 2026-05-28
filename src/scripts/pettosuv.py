# Copyright (c) 2026 PCViewer Jinfr
from typing import Dict, Tuple

import pydicom
import SimpleITK as sitk


def _parse_dicom_time(time_str: str) -> float:
    time_str = time_str
    if "." in time_str:
        time_str = time_str.split(".")[0]
    if len(time_str) == 5:
        time_str = "0" + time_str

    try:
        hours = float(time_str[0:2])
        minutes = float(time_str[2:4])
        seconds = float(time_str[4:6])
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        return 0.0


def _extract_dicom_metadata(dicom_dir: str) -> Tuple[Dict[str, float], sitk.Image]:
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir)
    reader.SetFileNames(dicom_names)
    pet_img = reader.Execute()

    ds = pydicom.dcmread(dicom_names[0])
    try:
        radio_info = ds.RadiopharmaceuticalInformationSequence[0]
    except (AttributeError, IndexError) as e:
        raise ValueError(f"DICOM文件缺少放射性药物信息: {dicom_names[0]}") from e

    metadata = {
        "patient_weight": float(getattr(ds, "PatientWeight", 70.0)),
        "study_time": getattr(ds, "AcquisitionTime", ds.StudyTime),
        "radio_start_time": getattr(radio_info, "RadiopharmaceuticalStartTime", ""),
        "total_dose": float(radio_info.RadionuclideTotalDose),
        "half_life": float(radio_info.RadionuclideHalfLife),
        "rescale_slope": float(getattr(ds, "RescaleSlope", 1.0)),
        "rescale_intercept": float(getattr(ds, "RescaleIntercept", 0.0)),
    }

    return metadata, pet_img


def pet_to_suv(dicom_dir: str, normalize: bool = False) -> sitk.Image:
    metadata, pet_img = _extract_dicom_metadata(dicom_dir)

    study_time = str(metadata["study_time"])
    radio_start_time = str(metadata["radio_start_time"])
    patient_weight = metadata["patient_weight"]
    total_dose = metadata["total_dose"]
    half_life = metadata["half_life"]
    rescale_slope = metadata["rescale_slope"]
    rescale_intercept = metadata["rescale_intercept"]

    time_acq = _parse_dicom_time(study_time)
    time_inj = _parse_dicom_time(radio_start_time)
    decay_time = time_acq - time_inj
    if decay_time < 0:
        decay_time += 24 * 3600

    decay_dose = total_dose * pow(2, -decay_time / half_life)
    suv_scale_factor = (1000.0 * patient_weight) / decay_dose

    if normalize:
        return (pet_img * rescale_slope + rescale_intercept) * suv_scale_factor

    return pet_img * suv_scale_factor
