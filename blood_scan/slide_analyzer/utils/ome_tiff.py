from PIL import Image, ImageSequence, TiffImagePlugin

im = Image.open("tubhiswt_C1_TP30.ome.tif")
frames = []
for i, frame in enumerate(ImageSequence.Iterator(im)):
	frame = frame.convert(frame.mode)
	info = TiffImagePlugin.ImageFileDirectory()
	info[56] = 54 + i
	info.tagtype[56] = 3
	frame.encoderinfo = {'tiffinfo': info}
	frames.append(frame)
with open("out.tiff", "w+b") as fp:
	with TiffImagePlugin.AppendingTiffWriter(fp) as tf:
		for frame in frames:
			frame.encoderconfig = ()
			TiffImagePlugin._save(frame, tf, "out.tiff")
			tf.newFrame()
