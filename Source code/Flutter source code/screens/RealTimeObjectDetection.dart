import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:tflite_v2/tflite_v2.dart';

class RealTimeObjectDetection extends StatefulWidget {
  final List<CameraDescription> cameras;

  const RealTimeObjectDetection({super.key, required this.cameras});

  @override
  _RealTimeObjectDetectionState createState() => _RealTimeObjectDetectionState();
}

class _RealTimeObjectDetectionState extends State<RealTimeObjectDetection> {
  late CameraController _controller;
  bool isModelLoaded = false;
  List<dynamic>? recognitions;
  int imageHeight = 0;
  int imageWidth = 0;
  bool isDetecting = false; // To check whether detection is active

  @override
  void initState() {
    super.initState();
    loadModel();
    initializeCamera(widget.cameras[0]); // Initialize the first camera
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> loadModel() async {
    String? res = await Tflite.loadModel(
      model: 'assets/welding_model.tflite',
      labels: 'assets/welding_labelmap.txt',
      // model: 'assets/detect.tflite',
      // labels: 'assets/labelmap.txt',
    );
    setState(() {
      isModelLoaded = res != null;
    });
  }

  void initializeCamera(CameraDescription description) async {
    _controller = CameraController(
      description,
      ResolutionPreset.high,
      enableAudio: false,
    );

    await _controller.initialize();

    if (!mounted) return;

    // Here we start the image stream only when we are in detection mode
    if (isDetecting) {
      _controller.startImageStream((CameraImage image) {
        if (isModelLoaded) {
          runModel(image);
        }
      });
    }

    setState(() {});
  }

///////////////////////////////////////////////////////////

  // Function to process the camera image and run YOLOv5 detection
  void runModel(CameraImage image) async {
    if (image.planes.isEmpty) return;

    // Directly passing the raw byte list from the CameraImage planes
    var recognitions = await Tflite.detectObjectOnFrame(
      bytesList: image.planes.map((plane) => plane.bytes).toList(),
      model: 'YOLO',  // Ensure YOLO is specified
      imageHeight: image.height,
      imageWidth: image.width,
      imageMean: 0, // YOLOv5 mean normalization
      imageStd: 255.0, // YOLOv5 standard deviation normalization
      numResultsPerClass: 1, // Adjust based on needs
      threshold: 0.5, // Confidence threshold
    );

    setState(() {
      this.recognitions = recognitions;
      imageHeight = image.height; // Update the height
      imageWidth = image.width;   // Update the width
    });
  }

///////////////////////////////////////////////////////////

  // void runModel(CameraImage image) async {
  //   if (image.planes.isEmpty) return;

  //   var recognitions = await Tflite.detectObjectOnFrame(
  //     bytesList: image.planes.map((plane) => plane.bytes).toList(),
  //     model: 'SSDMobileNet',
  //     imageHeight: image.height,
  //     imageWidth: image.width,
  //     imageMean: 127.5,
  //     imageStd: 127.5,
  //     numResultsPerClass: 1,
  //     threshold: 0.4,
  //   );

  //   setState(() {
  //     this.recognitions = recognitions;
  //     imageHeight = image.height; // Initialize the image
  //     imageWidth = image.width; // Initialize the image
  //   });
  // }

///////////////////////////////////////////////////////////

  void startObjectDetection() {
    if (!isDetecting) {
      isDetecting = true; // Change the state to detection
      _controller.startImageStream((CameraImage image) {
        if (isModelLoaded) {
          runModel(image);
        }
      });
    }
  }

  void stopObjectDetection() {
    _controller.stopImageStream(); // Stop the camera stream
    Navigator.pop(context); // Return to the previous screen
  }

  void pauseObjectDetection() {
    if (isDetecting) {
      _controller.stopImageStream(); // Stop the image stream
      setState(() {
        isDetecting = false; // Change the state to no detection
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_controller.value.isInitialized) {
      return Container();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Real-time Object Detection'),
        actions: [
          IconButton(
            icon: const Icon(Icons.stop),
            onPressed: stopObjectDetection, // Stop button
          ),
        ],
      ),
      body: Column(
        children: [
          SizedBox(
            width: MediaQuery.of(context).size.width,
            height: MediaQuery.of(context).size.height * 0.8,
            child: Stack(
              children: [
                CameraPreview(_controller), // Camera preview
                if (recognitions != null)
                  BoundingBoxes(
                    recognitions: recognitions!,
                    previewH: imageHeight.toDouble(),
                    previewW: imageWidth.toDouble(),
                    screenH: MediaQuery.of(context).size.height * 0.8,
                    screenW: MediaQuery.of(context).size.width,
                  ),
              ],
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: startObjectDetection, // Start button
                icon: Icon(
                  Icons.play_arrow,
                  size: 30,
                  color: isDetecting ? Colors.grey : Colors.green,
                ),
              ),
              const SizedBox(width: 20), // Space between buttons
              IconButton(
                onPressed: pauseObjectDetection, // Pause button
                icon: Icon(
                  Icons.pause,
                  size: 30,
                  color: isDetecting ? Colors.red : Colors.grey,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class BoundingBoxes extends StatelessWidget {
  final List<dynamic> recognitions;
  final double previewH;
  final double previewW;
  final double screenH;
  final double screenW;

  const BoundingBoxes({super.key, 
    required this.recognitions,
    required this.previewH,
    required this.previewW,
    required this.screenH,
    required this.screenW,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: recognitions.map((rec) {
        var x = rec["rect"]["x"] * screenW;
        var y = rec["rect"]["y"] * screenH;
        double w = rec["rect"]["w"] * screenW;
        double h = rec["rect"]["h"] * screenH;

        return Positioned(
          left: x,
          top: y,
          width: w,
          height: h,
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(
                color: Colors.red,
                width: 3,
              ),
            ),
            child: Text(
              "${rec["detectedClass"]} ${(rec["confidenceInClass"] * 100).toStringAsFixed(0)}%",
              style: TextStyle(
                color: Colors.red,
                fontSize: 15,
                background: Paint()..color = Colors.black,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
