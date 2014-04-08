---------------------------------
MultiQuicktime Add-On for Blender
---------------------------------

About:
------

MultiQuicktime is a blender add-on that lets you export multiple quicktime files from within blender's interface. It uses qt_tools for encoding videos, along with FFMPEG for some other more specific tasks. If I ever get around to it I might look at shifting the whole add-on over to using FFMPEG in order to make it more cross-platform.

You can find qt-tools at: http://omino.com/sw/qt_tools/

More about the add-on (original blog post): http://bensimonds.com/2013/10/14/multi-quicktime-add-on/

Installation:
-------------

Download Multiquicktime as a zip file and use blenders "Install Add-On from File" tool to add it to your add-ons directory.

Usage:
------

	1. Download, Install and Enable the add-on.
	2. Look in the Render Tab of Blender's Properties Editor, under Multi-Quicktime.
	3. Click “Add Multi Quicktime Output” to create at least one output file.
	4. Configure a new settings file or browse for an existing one if you’ve created one before. Clicking on the configure button will bring up the same settings dialog that Quicktime uses natively.
	5. Either manually generate your quicktime outputs with “Generate Outputs from Frames” (make sure you have rendered your animation first), or enable “Auto Generate After Render” and render your animation. In the latter case MultiQuicktime will output your videos afterwards.
