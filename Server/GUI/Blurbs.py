
WelcomeText : str = \
    "# __Ultimate Sensor Monitor__ \n" \
    "<br>" \
    "\nThe original source repository is at __[https://github.com/MarkVabulas/ultimon](https://github.com/MarkVabulas/ultimon)__. \n" \
    "<br>" \
    "Please check there for new updates and improvements, or to submit feedback or bug reports. \n" \
    "<br>" \
    "This interface is used to help setup and get the sensor software running " \
    "in the easiest way possible.  It should assist you in installing " \
    "the prerequisite softare, building everything from the source code, and " \
    "getting the server running.  If you decide to change your setup at a later " \
    "time, you can come back into this software and make further changes.  \n" \
    "<br>" \
    "This software is only responsible for the setup and configuration, the other " \
    "component does the heavy lifting and running behind the scenes.  \n" \
    "<br>" \
    "Each step of the process is a component of the whole.  Once the setup steps " \
    "are satisfied, then the software can be run by clicking 'Finish'.  Upon " \
    "startup, each step will check if it's already satisfied, and allow you to click " \
    "'Finish' immediately.\n " \
    "<br>" \
    "<br>" 

InstallPython : str = \
    "This step checks for the installation of Python.  Please click the button to " \
    "install it.  This will install Python onto your system for the current user.  " \
    "If the button is greyed out, then the software is found and you don't need to install it."

InstallNPM : str = \
			"This step checks for the installation of Node.js.  Please click the button to " \
			"install it.  This will install Node.JS onto your system for the current user.  " \
			"If the button is greyed out, then the software is found and you don't need to install it."

InstallLHM : str = \
    "This optional step will allow you to automatically download LibreHardwareMonitor from the " \
    "online repository and extracts the required dll files into the appropriate folder.  Use this " \
    "step only if you are planning to use LibreHardwareMonitor as your sensor data provider.\n\n" \
    "It's okay to perform this step even if you don't intend to use LibreHardwareMonitor."

GenerateKey : str = \
    "This procedure allows you to generate an SSL key for your server.  This means that no one " \
    "can snoop on the traffic between the server and the client.  It also makes it easier to get " \
    "the browsers to trust the connection.  It's recommended but entirely optional.  You should only " \
    "have to do this once, but you can replace the certificate any time."

BuildClient : str = \
    "This step will take the code for the HTML page and combine all of the images, scripts, " \
    "and styles together into a single .html file.  It must be run before the server starts, " \
    "but it can also be run while the server is running.  If the client page is modified while " \
    "the server is running, the clients will be notified and refresh their pages to match.  " \
    "This drastically simplifies making/testing changes because in many cases you don't need " \
    "to manually refresh your sensor/browser (this can break if you are making javascript " \
    "changes, and there are errors in the code).  The resulting .html file is placed in the " \
    "'Deploy\\static' folder."

BuildServer : str = \
    "This step will compile the python code into an executable that you can run.  It checks for consistency " \
    "in the modules that are installed and emits a file with minimal other requirements. The output exe, in " \
    "combination with any optional LibreHardwareMonitor files, and the static folder, could even be copied to " \
    "multiple machines.  This is the recommended way of running the server software for end-user deployments, " \
    "since the code is compiled and will be much faster.  If you plan on editing the server softare, then " \
    "running it in-place might be a good idea, but that's a little more complicated."

RunServer : str = \
    "Setup the values for running the server here.  It will save these values to a config file " \
    "in the Deploy directory.  You can then run the server from below, and this program can control " \
    "starting/stopping it, or you can acess the software directly in the Deploy directory with " \
    "the settings you configure here."
