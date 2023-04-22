import shutil
import os
import sys
from qqt import QtCore, QtGui, QtWidgets, qcreate
import qqt.gui as qui
from qqt.style import dark_palette_fusion
from genlib.path import Path

# wip module
# incomplete yet

class FileCopier(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(FileCopier, self).__init__(*args, **kwargs)
        self.pakRoot = None
        self.pakBat = None
        self.modDir = None

        self.setWindowTitle("Pak File Copier")

        self.mainLayout = qui.VBoxLayout(self)
        with self.mainLayout as ml:
            self.rootCopyDir = qui.StringField(label="Root Copy Dir Name")
            ml.add(self.rootCopyDir)

            splitter = qcreate(qui.Splitter, mode="horizontal")
            with splitter:
                lWidget = qcreate(QtWidgets.QWidget, layoutType=qui.VBoxLayout)
                with lWidget.layout() as lw:
                    self.reloadSourceBtn = qui.Button('reload source')
                    lw.add(self.reloadSourceBtn)

                    self.sourceFile = FileBrowser()
                    cm = qui.ContextMenu(self.sourceFile.view)
                    cm.addCommand("copy files", self.copyFiles)
                    # cm.addCommand("delete files", self.deleteFiles)

                    lw.add(self.sourceFile)

                rWidget = qcreate(QtWidgets.QWidget, layoutType=qui.VBoxLayout)
                with rWidget.layout() as rw:
                    self.reloadTargetBtn = qui.Button('reload target')
                    rw.add(self.reloadTargetBtn)

                    self.targetFile = FileBrowser()
                    cm = qui.ContextMenu(self.targetFile.view)
                    cm.addCommand("delete files", self.deleteFiles)
                    rw.add(self.targetFile)

            qcreate(qui.SeparatorLine, mode="horizontal")
            self.makePakBtn = qui.Button("MAKE PAK")
            ml.add(self.makePakBtn)
            qcreate(qui.SeparatorLine, mode="horizontal")
            self.copyPakBtn = qui.Button("copy PAK to mod dir")
            ml.add(self.copyPakBtn)

            qcreate(qui.Spacer, mode="vertical")

            ml.setRatio(0,1,0,0,0,0,0,0,0,0)

        self.reloadSourceBtn.clicked.connect(self.reloadSource)
        self.reloadTargetBtn.clicked.connect(self.reloadTarget)
        self.makePakBtn.clicked.connect(self.makePak)
        self.copyPakBtn.clicked.connect(self.copyPak)

    def setRootCopyDirName(self, dirName):
        self.rootCopyDir.setValue(dirName)

    def makePak(self):
        pakCmd = Path(self.pakRoot) / self.pakBat
        print(pakCmd)
        os.system(pakCmd)

    def copyPak(self):
        sourcePath = self.pakRoot / "NewMod.pak"
        targetPath = self.modDir / "NewMod.Pak"

        sourcePath.copy(targetPath)

    def setSourceRoot(self, path):
        self.sourceRoot = path

    def setTargetRoot(self, path):
        self.targetRoot = path

    def reloadSource(self):
        self.sourceFile.reload_root_dir(self.sourceRoot)

    def reloadTarget(self):
        self.targetFile.reload_root_dir(self.targetRoot)

    def copyFiles(self):
        checkDir = self.rootCopyDir.getValue().lower()

        targetBaseDir = None
        targetRoot = Path(self.targetRoot).normpath().replace("\\","/")
        print(targetRoot)
        tokens = targetRoot.split("/")
        for idx,tok in enumerate(tokens):
            if tok.lower() == checkDir:
                partialPath = "/".join(tokens[0:idx+1])
                targetBaseDir = partialPath
                break

        files = self.sourceFile.getSelectedFiles()

        for eachFile in files:
            eachFile = Path(eachFile)
            # baseName = eachFile.basename()
            # print(baseName)

            # dirName = eachFile.dirname()

            tokens = eachFile.split("/")
            # print(tokens)

            partialPath = None

            for idx,tok in enumerate(tokens):
                if tok.lower() == checkDir:
                    partialPath = "/".join(tokens[idx+1:])
                    # print(partialPath)
                    break

            if partialPath:
                targetPath = Path(targetBaseDir) / partialPath

                targetDir = targetPath.dirname()

                if not targetDir.exists():
                    targetDir.makedirs()


                if targetPath.exists():
                    targetPath.remove()

                shutil.copyfile(eachFile, targetPath)

                # print(eachFile)
                # print(targetPath)

    def deleteFiles(self):
        files = self.targetFile.getSelectedFiles()

        if files:
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   "Are you sure to delete selected files?", QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                for f in files:
                    f = Path(f)
                    if f.exists():
                        if f.isdir():
                            # f.rmdir()
                            f.rmtree()
                        else:
                            f.remove()

                    # Path(f).remove()

            #     self.model.rmdir(selected)
            #     shutil.rmtree(fpath)

    def setPakRoot(self, pakRoot):
        self.pakRoot = Path(pakRoot)

    def setPakBat(self, pakBat):
        self.pakBat = Path(pakBat)

    def setModDir(self, modDir):
        self.modDir = Path(modDir)

class FileView(QtWidgets.QTreeView):
    def __init__(self, *args,**kwargs):
        super(FileView, self).__init__(*args,**kwargs)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDragEnabled(True)


    def dropEvent(self, event):
        print("HEREER")

class FileSystem(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(FileSystem, self).__init__(*args, **kwargs)

        self._layout = qui.VBoxLayout(self)
        with self._layout as ly:
            self.filterField = qui.StringField()
            ly.add(self.filterField)

            self.view = FileView()
            ly.add(self.view)


        self.model = QtWidgets.QFileSystemModel()

        self.view.setModel(self.model)


        self.filterModel = MyFilter(self)
        self.filterModel.setSourceModel(self.model)
        self.filterModel.setDynamicSortFilter(True)
        self.view.setModel(self.filterModel)
        # self.view.setRootIndex(self.filterModel.mapFromSource(self.model.index(r"E:\reference")))

        self.selModel = self.view.selectionModel()
        # val = "aaa"
        # self.filterModel.setFilterRegExp(val)
        self.filterField.textEdited.connect(self.doFilter)
        self.filterModel.setFilterKeyColumn(0)
        cs = QtCore.Qt.CaseInsensitive
        self.filterModel.setFilterCaseSensitivity(cs)

    def doFilter(self):
        val = self.filterField.getValue()
        self.filterModel.filterString = val
        # self.filterModel.setFilter(val)
        # self.view.setRootIndex(self.filterModel.mapFromSource(self.model.index(r"E:\reference")))
        self.filterModel.setFilterRegExp(val)
        # self.view.setRootIndex(self.filterModel.mapFromSource(self.model.index(r"E:\reference")))

    def expandAll(self):
        for idx in range(0,10):
            self.view.expandAll()
            QtWidgets.QApplication.processEvents()

class FileBrowser(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):

        super(FileBrowser, self).__init__(*args, **kwargs)
        self._initUI()
        self._connectsignals()

    def _initUI(self):
        layout = qui.VBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        with layout:
            # self.reloadBtn = qcreate(qui.Button,'reload source')

            self.fileBrowser = qcreate(FileSystem)
            self.model = self.fileBrowser.model
            self.view = self.fileBrowser.view
            self.filterModel = self.fileBrowser.filterModel

            self.view.hideColumn(1)
            self.view.hideColumn(2)
            self.view.hideColumn(3)
            self.view.header().hide()

            # self.contextMenu = qui.ContextMenu(self.view)
            # self.contextMenu.addCommand("copy files", self.copyFiles)
            # self.contextMenu.addCommand("delete files", self.deleteFiles)

            # self.model.setRootPath(r"e:\reference")
            # self.view.setModel(self.model)
            # self.view.setRootIndex(self.filterModel.mapFromSource(self.model.index(r"E:\reference")))
            # self.view.selectionModel()

            self.selModel = self.view.selectionModel()

        self.setAcceptDrops(True)

    def dragEnterEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if ( urls and urls[0].scheme() == 'file' ):
            event.acceptProposedAction()

    def dragMoveEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if ( urls and urls[0].scheme() == 'file' ):
            event.acceptProposedAction()

    def dropEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if urls:
            for url in urls:
                if url.scheme() == "file":

                    # for some reason, this doubles up the intro slash
                    filepath = str(urls[0].path())[1:]
                    print("FILEPATH {}".format(filepath))

                    # self.setText(filepath)
                    # self.editingFinished.emit()


    def _connectsignals(self):
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuCallback)
        # self.reloadBtn.clicked.connect(self.reload_root_dir)


    def reload_root_dir(self, rootDir):
        self._rootDir = rootDir
        self.setDir(self._rootDir)
        self.fileBrowser.expandAll()

    def contextMenuCallback(self, event, *args, **kwargs):
        self.mainMenu = QtWidgets.QMenu()
        self.mainMenu.exec_(event.globalPos())

    def setDir(self, cdir):
        self.model.setRootPath(cdir)
        self.view.setRootIndex(self.filterModel.mapFromSource(self.model.index(cdir)))


    def getSelectedFiles(self):
        files = []
        sels = self.selModel.selectedIndexes()
        for selected in sels:
            selected = self.filterModel.mapToSource(selected)
            fpath = self.model.filePath(selected)
            if fpath not in files:
                files.append(fpath)

        return files




    def getSelectedPaths(self):
        indexes = self.selModel.selectedIndexes()
        indexes = [self.filterModel.mapToSource(idx) for idx in indexes]
        items = [self.model.filePath(idx) for idx in indexes if idx.column() == 0]
        return items


class MyFilter(QtCore.QSortFilterProxyModel):
    def __init__(self,*args,**kwargs):
        super(MyFilter, self).__init__(*args,**kwargs)
        self.filterString = None

    def filterAcceptsRow(self,source_row,source_parent):
        if self.filterString:
            model = self.sourceModel()
            if source_parent == model.index(model.rootPath()):
                return super(MyFilter, self).filterAcceptsRow(source_row, source_parent)
            else:
                return True
        else:
            return True


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyside())

    palette = dark_palette_fusion.QDarkPalette()
    palette.set_app(app)



    ui = FileCopier()
    ui.show()
    ui.setSourceRoot(r"E:\unreal\projects\ue4_20\arise\saved\cooked\windowsnoeditor\arise\content\release\arise\graphic\chr")

    QtWidgets.QApplication.processEvents()
    ui.reloadSource()


    ui.setTargetRoot(r"e:\games\mod\arise\u4pak\arise\content\release\arise\graphic\chr")


    QtWidgets.QApplication.processEvents()
    ui.reloadTarget()

    ui.setRootCopyDirName("content")

    ui.setPakRoot(r"E:\games\mod\Arise\u4pak")

    ui.setPakBat("Repack_Arise.bat")

    # ui.showMaximized()

    ui.setModDir(r"E:\games\steam\steamapps\common\Tales of Arise\Arise\Content\Paks\~mods")

    sys.exit(app.exec_())
