from __main__ import vtk, qt, ctk, slicer
import numpy as np
import os
import moviepy.video.io.ImageSequenceClip

class takeScreenshots:
  def __init__(self, parent):
    parent.title = "takeScreenshots"
    parent.categories = ["Examples"]
    parent.dependencies = []
    parent.contributors = ["Firmin"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    You can use this module to take screenshots automatically with your desired step size,thickness.
    """
    parent.acknowledgementText = """
    This file was originally developed by Firmin Shao """ # replace with organization, grant and thanks.
    self.parent = parent

#
# takeScreenshots
#

class takeScreenshotsWidget:
	def __init__(self,parent):
		self.parent = parent
		self.layout = parent.layout()

	def setup(self):

		inputsCollapsibleButton = ctk.ctkCollapsibleButton()
		inputsCollapsibleButton.text = "Inputs"
		self.layout.addWidget(inputsCollapsibleButton)
		# Layout within the inputs collapsible button
		inputs_formLayout = qt.QFormLayout(inputsCollapsibleButton)

		self.step_size_box = ctk.ctkDoubleSpinBox()
		self.step_size_box.value = 0.1
		self.step_size_box.singleStep = 0.1
		self.step_size_box.setToolTip('Along the specified direction, the increment of each ROI area movement')
		inputs_formLayout.addRow('Step Size',self.step_size_box)

		self.thickness_box = ctk.ctkDoubleSpinBox()
		self.thickness_box.value = 0.1
		self.thickness_box.singleStep = 0.1
		self.thickness_box.setToolTip('Along the specified direction, the range of each ROI area movement')
		inputs_formLayout.addRow("Thickness", self.thickness_box)

		self.starting_range_box = ctk.ctkDoubleSpinBox()
		self.starting_range_box.singleStep = 0.1
		self.starting_range_box.minimum = -1000
		self.starting_range_box.maximum = 1000
		self.starting_range_box.value = -10
		self.starting_range_box.setToolTip('ROI start position')
		inputs_formLayout.addRow("Starting Range", self.starting_range_box)

		self.ending_range_box = ctk.ctkDoubleSpinBox()
		self.ending_range_box.singleStep = 0.1
		self.ending_range_box.minimum = -1000
		self.ending_range_box.maximum = 1000
		self.ending_range_box.value = 10
		self.ending_range_box.setToolTip('ROI end position')
		inputs_formLayout.addRow("Ending Range", self.ending_range_box)

		self.volume_choice_box = qt.QComboBox()
		self.volume_choice_box.addItems(['The first rendered volume','The Second rendered volume','The Third rendered volume'])
		self.volume_choice_box.setToolTip('Select the volume you want to slice which corresponds to the volume in volume rendering module')
		inputs_formLayout.addRow('Select Rendered Volume',self.volume_choice_box)

		plane_gridLayout = qt.QGridLayout(inputsCollapsibleButton)
		self.P_A_orientation_btn = qt.QRadioButton('Coronal')
		self.P_A_orientation_btn.setChecked(True)
		self.P_A_orientation_btn.setToolTip('Slice From Posterior To Anterior')
		self.I_S_orientation_btn = qt.QRadioButton('Axial')
		self.I_S_orientation_btn.setToolTip('Slice From Inferior To Superior')
		self.L_R_orientation_btn = qt.QRadioButton('Sagittal')
		self.L_R_orientation_btn.setToolTip('Slice From Left To Right')
		plane_gridLayout.addWidget(self.P_A_orientation_btn,0,0)
		plane_gridLayout.addWidget(self.I_S_orientation_btn,0,1)
		plane_gridLayout.addWidget(self.L_R_orientation_btn,0,2)
		inputs_formLayout.addRow('Select Plane',plane_gridLayout)

		self.file_dir_btn = ctk.ctkDirectoryButton()
		self.file_dir_btn.directory = "C:/slices/temp"
		self.file_dir_btn.setToolTip('Where to save the images')
		inputs_formLayout.addRow('Select directory',self.file_dir_btn)


		applyCollapsibleButton = ctk.ctkCollapsibleButton()
		applyCollapsibleButton.text = "Apply"
		self.layout.addWidget(applyCollapsibleButton)
		apply_formLayout = qt.QFormLayout(applyCollapsibleButton)

		self.adjust_btn = qt.QPushButton("Adjust Volume Size")
		self.adjust_btn.connect('clicked(bool)',self.onAdjustmentBtnClicked)
		self.adjust_btn.setToolTip('Resize the rendered image based on the size of the original data, keeping both the same')
		apply_formLayout.addRow(self.adjust_btn)

		self.init_pos_btn = qt.QPushButton("Initialize Position")
		self.init_pos_btn.connect('clicked(bool)',self.onInitPosBtnClicked)
		self.init_pos_btn.setToolTip('Move the ROI area to the initial position of the specified range')
		apply_formLayout.addRow(self.init_pos_btn)

		apply_gridLayout = qt.QGridLayout(applyCollapsibleButton)
		self.create_movie_box = qt.QCheckBox('Create A Movie')
		self.create_movie_box.setToolTip('Generate animation from pictures(.mp4)')
		self.save_btn = qt.QPushButton("Take Screenshots")
		self.save_btn.setToolTip('Within the specified range, all the corresponding pictures are generated according to the set step size and thickness. If the Create A Movie button is selected, an additional video file will be generated')
		self.save_btn.connect('clicked(bool)',self.onsaveSSbtnClicked)
		apply_gridLayout.addWidget(self.save_btn,0,0,1,6)
		apply_gridLayout.addWidget(self.create_movie_box,0,6,1,1)
		apply_formLayout.addRow(apply_gridLayout)
	
		self.layout.addStretch(1)

		self.flag = True # a trick to keep original roi info 

	def onsaveSSbtnClicked(self):

		startingRoiCenter,roi,orientation = self.onInitPosBtnClicked()
		if orientation == 1:
			# P-A
			self.auto_screenshot_PA(startingRoiCenter,roi)
		if orientation == 2:
			# I-S
			self.auto_screenshot_IS(startingRoiCenter,roi)		
		if orientation == 3:
			# L-R
			self.auto_screenshot_LR(startingRoiCenter,roi)

		if self.create_movie_box.isChecked():
			self.create_a_movie()

		qt.QMessageBox.information(slicer.util.mainWindow(),'Prompt Window','Screenshots Already Saved!')
		

	def onInitPosBtnClicked(self):
		if self.volume_choice_box.currentIndex == 0:
			# first volume 
			roi = slicer.mrmlScene.GetNodeByID('vtkMRMLAnnotationROINode1')
		elif self.volume_choice_box.currentIndex == 1:
			# second volume 
			roi = slicer.mrmlScene.GetNodeByID('vtkMRMLAnnotationROINode2')
		elif self.volume_choice_box.currentIndex == 2:
			# third volume 
			roi = slicer.mrmlScene.GetNodeByID('vtkMRMLAnnotationROINode3')

		# keep original roi info as object attributes
		if self.flag:
			origin = np.zeros((3)) 
			roi.GetXYZ(origin)
			radius = np.zeros((3)) 
			roi.GetRadiusXYZ(radius)
			self.origin = origin
			self.radius = radius
			self.flag = False

		# restore roi range
		roi.SetXYZ(self.origin)
		roi.SetRadiusXYZ(self.radius)

		if self.P_A_orientation_btn.isChecked():
			# P-A = 1 
			startingRoiCenter,roi = self.init_PA_pos(roi)
			orientation = 1
			slicer.app.layoutManager().threeDWidget('View1').threeDView().lookFromAxis(6)
		elif self.I_S_orientation_btn.isChecked():
			# I-S = 2
			startingRoiCenter,roi = self.init_IS_pos(roi)
			orientation = 2
			slicer.app.layoutManager().threeDWidget('View1').threeDView().lookFromAxis(4)
		elif self.L_R_orientation_btn.isChecked():
			# L-R = 3
			startingRoiCenter,roi = self.init_LR_pos(roi)
			orientation = 3
			slicer.app.layoutManager().threeDWidget('View1').threeDView().lookFromAxis(2)
		return startingRoiCenter,roi,orientation

	def read_all_png_files(self,path):
		file_list = os.listdir(path)
		starting = 12
		ending = -4
		file_list.sort(key = lambda file_name:int(file_name[starting:ending]))
		image_list = []
		for file_name in file_list:
			file_path = os.path.join(path,file_name)
			image_list.append(file_path)
		return image_list

	def create_a_movie(self):
		image_list = self.read_all_png_files(self.file_dir_btn.directory)
		clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_list, fps=30)
		clip.write_videofile(self.file_dir_btn.directory+'/my_movie.mp4')

	def onAdjustmentBtnClicked(self):
		panelDockWidget = slicer.util.mainWindow().findChildren('QDockWidget','PanelDockWidget')[0]
		slicer.util.mainWindow().resizeDocks([panelDockWidget],[800], qt.Qt.Horizontal) 
		view = slicer.app.layoutManager().threeDWidget(0).threeDView()
		view.resetFocalPoint()
		renderWindow = view.renderWindow()
		renderers = renderWindow.GetRenderers()
		renderer = renderers.GetItemAsObject(0)
		camera = renderer.GetActiveCamera() 
		ZoomScaleH = (0.025*(view.height)-0.0872)*2
		camera.SetParallelScale(ZoomScaleH) 

	# Capture RGBA image
	def take_one_screen_shot(self,suffix=0,folder_path=None):
		view = slicer.app.layoutManager().threeDWidget(0).threeDView()
		renderWindow = view.renderWindow()
		renderWindow.SetAlphaBitPlanes(1)
		wti = vtk.vtkWindowToImageFilter()
		wti.SetInputBufferTypeToRGBA()
		wti.SetInput(renderWindow)
		writer = vtk.vtkPNGWriter()
		file_name = folder_path+"/screen_shots"+str(suffix)+".png"
		print(file_name)
		writer.SetFileName(file_name)
		writer.SetInputConnection(wti.GetOutputPort())
		writer.Write()


	def init_PA_pos(self,roi):
		starting_range = self.starting_range_box.value
		thickness = self.thickness_box.value

		origin = np.zeros((3)) 
		roi.GetXYZ(origin)
		origin[1] = 0 # bias
		startingRoiCenter = np.array([0,starting_range+thickness/2,0]) + origin # allocate position vector

		radius = np.zeros((3)) #pre-allocate
		roi.GetRadiusXYZ(radius) # fill in
		radius[1] = 0
		startingRoiRadius = np.array([0,thickness/2,0]) + radius

		roi.SetXYZ(startingRoiCenter)
		roi.SetRadiusXYZ(startingRoiRadius)
		return startingRoiCenter,roi

	def init_IS_pos(self,roi):
		starting_range = self.starting_range_box.value
		thickness = self.thickness_box.value

		origin = np.zeros((3)) 
		roi.GetXYZ(origin)
		origin[2] = 0 # bias
		startingRoiCenter = np.array([0,0,starting_range+thickness/2]) + origin # allocate position vector

		radius = np.zeros((3)) #pre-allocate
		roi.GetRadiusXYZ(radius) # fill in
		radius[2] = 0
		startingRoiRadius = np.array([0,0,thickness/2]) + radius

		roi.SetXYZ(startingRoiCenter)
		roi.SetRadiusXYZ(startingRoiRadius)
		return startingRoiCenter,roi

	def init_LR_pos(self,roi):
		starting_range = self.starting_range_box.value
		thickness = self.thickness_box.value

		origin = np.zeros((3)) 
		roi.GetXYZ(origin)
		origin[0] = 0 # bias
		startingRoiCenter = np.array([starting_range+thickness/2,0,0]) + origin # allocate position vector

		radius = np.zeros((3)) #pre-allocate
		roi.GetRadiusXYZ(radius) # fill in
		radius[0] = 0
		startingRoiRadius = np.array([thickness/2,0,0]) + radius

		roi.SetXYZ(startingRoiCenter)
		roi.SetRadiusXYZ(startingRoiRadius)
		return startingRoiCenter,roi		

	def auto_screenshot_PA(self,startingRoiCenter,roi):
		step_size = self.step_size_box.value
		thickness = self.thickness_box.value
		starting_range = self.starting_range_box.value
		ending_range = self.ending_range_box.value
		folder_path = self.file_dir_btn.directory


		# threeDViewNode = slicer.app.layoutManager().threeDWidget(0).threeDView()
		# volumeRenderingNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLVolumeRenderingDisplayNode")
		# if not volumeRenderingNode.IsDisplayableInView(threeDViewNode.GetID()):
		# 	volumeRenderingNode.AddViewNodeID(threeDViewNode.GetID())




		suffix = 0
		for centerSuperiorOffset in np.arange(0,ending_range-starting_range,step_size):
			newRoiCenter = startingRoiCenter + np.array([0,centerSuperiorOffset,0])
			roi.SetXYZ(newRoiCenter)
			self.take_one_screen_shot(suffix,folder_path)
			suffix+=1
		return suffix


	def auto_screenshot_IS(self,startingRoiCenter,roi):
		step_size = self.step_size_box.value
		thickness = self.thickness_box.value
		starting_range = self.starting_range_box.value
		ending_range = self.ending_range_box.value
		folder_path = self.file_dir_btn.directory

		suffix = 0
		for centerSuperiorOffset in np.arange(0,ending_range-starting_range,step_size):
			newRoiCenter = startingRoiCenter + np.array([0,0,centerSuperiorOffset])
			roi.SetXYZ(newRoiCenter)
			self.take_one_screen_shot(suffix,folder_path)
			suffix+=1
		return suffix

	def auto_screenshot_LR(self,startingRoiCenter,roi):
		step_size = self.step_size_box.value
		thickness = self.thickness_box.value
		starting_range = self.starting_range_box.value
		ending_range = self.ending_range_box.value
		folder_path = self.file_dir_btn.directory

		suffix = 0
		for centerSuperiorOffset in np.arange(0,ending_range-starting_range,step_size):
			newRoiCenter = startingRoiCenter + np.array([centerSuperiorOffset,0,0])
			roi.SetXYZ(newRoiCenter)
			self.take_one_screen_shot(suffix,folder_path)
			suffix+=1
		return suffix

