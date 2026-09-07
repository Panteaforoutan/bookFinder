import { useState } from "react";
import { boxStyle } from "../utils/image";
import LocateProgress from "./LocateProgress";

function LocateImagePreview({ imageUrl, box, currentStage }) {
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
      {currentStage && (
        <div className="locate-progress-overlay">
          <LocateProgress currentStage={currentStage} />
        </div>
      )}
    </div>
  );
}

export default LocateImagePreview;