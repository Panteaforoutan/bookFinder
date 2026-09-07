import { useState } from "react";
import { boxStyle } from "../utils/image";

function LocateImagePreview({ imageUrl, box }) {
  const [imageSize, setImageSize] = useState(null);

  if (!imageUrl) return null;

  return (
    <div className="locate-image-wrapper">
      <img
        src={imageUrl}
        alt="Uploaded shelf"
        onLoad={(e) =>
          setImageSize({
            width: e.target.naturalWidth,
            height: e.target.naturalHeight,
          })
        }
        style={{ width: "100%", display: "block" }}
      />
      {box && imageSize && (
        <div className="locate-box" style={boxStyle(box, imageSize)} />
      )}
    </div>
  );
}

export default LocateImagePreview;