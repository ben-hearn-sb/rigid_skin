from PyQt4 import QtGui, QtCore

class ProcessDialog(QtGui.QDialog):
	def __init__(self, parent=None, fixedHeight=-1, enableButton=False):
		QtGui.QDialog.__init__(self)
		if fixedHeight != -1:
			self.setFixedHeight(fixedHeight)

		self.enableButtonFlag = enableButton
		self.resize(450, 350)
		self.setModal(True)
		self.setWindowTitle('Processing....')
		self.setObjectName('PROCESS_DIALOG')
		self.activityLog = QtGui.QListWidget()

		self.btnOK = QtGui.QPushButton('OK')
		self.btnOK.setDisabled(True)
		self.btnCancel = QtGui.QPushButton('Cancel')

		self.layout = QtGui.QVBoxLayout()
		self.layout.setSpacing(0)
		self.layout.addWidget(self.activityLog, 0)
		self.layout.setContentsMargins(0,0,0,0)
		self.setLayout(self.layout)

		self.btnOK.clicked.connect(self.close)
		#self.btnCancel.clicked.connect(self.cancelExport)

	def closeEvent(self, event):
		""" On close we are removing the Qt window from memory """
		self.deleteLater()
		event.accept()

	def cancelExport(self):
		self.updateLog(process='Cancelled Export. Undoing process...', error=True)
		#self.enableButton()
		self.btnCancel.setDisabled(True)
		self.activateWindow()


	def updateLog(self, process, success=False, warning=False, error=False, textColor=None):
		import datetime
		time = datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)
		time = str(time)
		processWidget = QtGui.QListWidgetItem(time + ': ' +process)
		processWidget.setFlags(QtCore.Qt.ItemIsEnabled)
		if warning == True:
			processWidget.setTextColor(QtGui.QColor('orange'))
		if error == True:
			processWidget.setTextColor(QtGui.QColor('red'))
		if success == True:
			processWidget.setBackgroundColor(QtGui.QColor('green'))
		self.activityLog.addItem(processWidget)
		self.activityLog.scrollToItem(processWidget)
		QtGui.qApp.processEvents()

	def clearLog(self):
		self.activityLog.clear()