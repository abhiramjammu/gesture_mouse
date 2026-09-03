const videoElement = document.getElementsByClassName('input_video')[0];
const canvasElement = document.getElementsByClassName('output_canvas')[0];
const canvasCtx = canvasElement.getContext('2d');
const virtualCursor = document.getElementById('virtual-cursor');
const loadingText = document.querySelector('.loading');

let isClicking = false;
let screenWidth = window.innerWidth;
let screenHeight = window.innerHeight;

window.addEventListener('resize', () => {
    screenWidth = window.innerWidth;
    screenHeight = window.innerHeight;
});

function onResults(results) {
    // Hide loading text once we get first frame
    loadingText.style.display = 'none';

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
    
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        virtualCursor.style.display = 'block';
        
        for (const landmarks of results.multiHandLandmarks) {
            drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 5});
            drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 2});
            
            const indexTip = landmarks[8];
            const thumbTip = landmarks[4];
            
            // X is inverted because we mirrored the video via CSS
            const cursorX = (1 - indexTip.x) * screenWidth;
            const cursorY = indexTip.y * screenHeight;
            
            virtualCursor.style.left = `${cursorX}px`;
            virtualCursor.style.top = `${cursorY}px`;
            
            // Distance for pinch
            const dx = indexTip.x - thumbTip.x;
            const dy = indexTip.y - thumbTip.y;
            const distance = Math.sqrt(dx*dx + dy*dy);
            
            if (distance < 0.06) {
                if (!isClicking) {
                    isClicking = true;
                    virtualCursor.classList.add('clicking');
                    
                    // Trigger click at the current cursor location on screen
                    const element = document.elementFromPoint(cursorX, cursorY);
                    if (element && element.tagName === 'BUTTON') {
                        element.click();
                    }
                }
            } else {
                isClicking = false;
                virtualCursor.classList.remove('clicking');
            }
        }
    } else {
        virtualCursor.style.display = 'none';
    }
    canvasCtx.restore();
}

const hands = new Hands({locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
}});
hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.7
});
hands.onResults(onResults);

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await hands.send({image: videoElement});
    },
    width: 640,
    height: 480
});
camera.start();
