export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

export function boxStyle([left, top, right, bottom], { width, height }) {
  return {
    position: "absolute",
    left: `${(left / width) * 100}%`,
    top: `${(top / height) * 100}%`,
    width: `${((right - left) / width) * 100}%`,
    height: `${((bottom - top) / height) * 100}%`,
  };
}

// iOS Safari often reports an empty file.type for HEIC photos, so the
// filename extension is checked as a fallback rather than relying on
// the MIME type alone.
export function isHeic(file) {
  const type = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  return (
    type === "image/heic" ||
    type === "image/heif" ||
    name.endsWith(".heic") ||
    name.endsWith(".heif")
  );
}