import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:realtime_obj_detection/screens/SplashScreen.dart'; // Ensure this path is correct

void main() async {
  WidgetsFlutterBinding.ensureInitialized(); // Ensures that the Flutter framework is initialized
  final cameras = await availableCameras(); // Fetch available cameras
  runApp(MyApp(cameras: cameras)); // Pass the list of cameras to the app
}

class MyApp extends StatelessWidget {
  final List<CameraDescription> cameras;

  const MyApp({super.key, required this.cameras});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: SplashScreen(cameras: cameras),  // Navigates to the splash screen
    );
  }
}
