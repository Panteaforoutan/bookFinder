import { forwardRef, useImperativeHandle, useRef, useState } from "react";
import heic2any from "heic2any";
import { ACCEPTED_IMAGE_TYPES, isHeic } from "../utils/image";

const ImageUploadField = forwardRef(function ImageUploadField(
  { onImageSelected, converting, setConverting },
  ref
) {
  const [fileError, setFileError] = useState("");
  const fileInputRef = useRef(null);

  useImperativeHandle(ref, () => ({
    reset() {
      setFileError("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
  }));

  async function handleFileSelect(e) {
    const file = e.target.files[0];
    setFileError("");

    if (!file) {
      onImageSelected(null);
      return;
    }

    if (isHeic(file)) {
      setConverting(true);
      try {
        const converted = await heic2any({ blob: file, toType: "image/jpeg" });
        onImageSelected(Array.isArray(converted) ? converted[0] : converted);
      } catch {
        setFileError("Couldn't convert this HEIC image. Please try a different photo.");
        onImageSelected(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      } finally {
        setConverting(false);
      }
      return;
    }

    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      setFileError("Please select a JPEG, PNG, or WEBP image.");
      onImageSelected(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    onImageSelected(file);
  }

  return (
    <>
      <input
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
        ref={fileInputRef}
        disabled={converting}
        onChange={handleFileSelect}
      />
      {converting && <p>Converting HEIC image...</p>}
      {fileError && <p className="error">{fileError}</p>}
    </>
  );
});

export default ImageUploadField;