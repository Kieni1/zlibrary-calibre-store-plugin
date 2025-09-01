Building a Static Tor Binary for ARMv7

This project provides a Docker-based solution to create a statically linked Tor binary suitable for devices like the Remarkable 2. The provided Dockerfile handles all the necessary steps, including installing build tools and compiling the libevent and openssl dependencies from source.
How to Use

Follow these steps to build the tor binary and extract it to your local machine.

Save the Dockerfile: Ensure the provided Dockerfile is in the same directory as this README.md file.

Build the Docker Image: Open a terminal in the project directory and run the following command. This will create a build environment containing all the necessary tools and the compiled tor binary.

    docker build . -t tor-armv7-builder

Create Output Directory: Before extracting the file, ensure a destination directory exists on your local machine.

    mkdir -p output

Extract the Tor Binary: Use the following commands to create a temporary container and copy the compiled tor binary from inside the container to your local output directory.

    # Create a container from the image to access its files.
    # The container will be removed at the end.
    CONTAINER_ID=$(docker create tor-armv7-builder)

    # Copy the tor binary from the container's /output directory to your local output folder.
    docker cp $CONTAINER_ID:/output/tor output/

    # Clean up and remove the temporary container to save space.
    docker rm $CONTAINER_ID

The final statically linked tor binary will be located in the output directory and can be transferred to your ARMv7 device.
