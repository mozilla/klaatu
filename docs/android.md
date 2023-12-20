# Klaatu for Android

The preferred method of running the android tests are using the provided docker image. The steps below outline how that can be done.

## Docker

Close your android studio instance if it is running. Navigate to your `platform-tools` folder where `adb` is located and run the following command:

```sh
./adb.exe -a nodaemon server start
```
This will start adb as a server. You can now open Android Studio and start an emulator, or you can start an emulator in another terminal as follows:

```sh
./emulator -avd Pixel_3a_API_34_extension_level_7_x86_64
```

To see your available emulators run this command `./emulator -list-avds`. Copy the name of the emulator that is displayed and paste it in the above command replacing the `Pixel_3a_API_34_extension_level_7_x86_64`.

Once the emulator starts, run the following command:

```sh
docker run --add-host=host.docker.internal:host-gateway -it -e EXPERIMENT_SLUG="experiment-slug" -e ANDROID_ADB_SERVER_ADDRESS="host.docker.internal" klaatu-android
```

The tests should run on the emulated device.