import { Lottie } from "lottie-react";
import scanAnim from "../assets/scanner.json";
import ocrAnim from "../assets/loading.json";
import matchAnim from "../assets/scanner.json";



function LocateProgress({ currentStage }) {
    const stageLabels = {
        scan: "Scanning shelf...",
        ocr: "Reading titles...",
        match: "Matching...",
    };

    const animations = {
        scan: scanAnim,
        ocr: ocrAnim,
        match: matchAnim,
    };

    return (
        <div>
            <Lottie
                src={animations[currentStage]}
                autoplay
                loop
                style={{ width: 300, height: 300 }}
            />
            <p>{stageLabels[currentStage]}</p>
        </div>
    );
}

export default LocateProgress;
