from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox
import os, sys
import json
import numpy as np
from enum import Enum
import pandas as pd
# app. is necessary
from app.dta_toolbox_ui import Ui_MainWindow


class DTA_Toolbox(Ui_MainWindow):
    def __init__(self):
        super(DTA_Toolbox, self).__init__()
        # init all flags and containers
        self.files_list = []
        self.labels_flag = False
        # 0-txt,1-csv
        self.labels_index = 0
        self.data_flag = False
        # 0-csv,1-mysql,2-mongoDB
        self.data_index = 0

    def setupUi(self, MainWindow):
        # Father's UI
        Ui_MainWindow.setupUi(self, MainWindow)
        # Menu
        self.actionQuit.triggered.connect(on_Action_quit)
        # Push Buttons
        self.pushButton_files.clicked.connect(self.on_pushButton_files_clicked)
        self.pushButton_extract.clicked.connect(self.on_pushButton_extract_clicked)
        # Checkbox
        self.groupBox_labels.clicked.connect(self.on_groupBox_labels_clicked)
        self.groupBox_data.clicked.connect(self.on_groupBox_data_clicked)
        # Radio Buttons
        self.radioButton_labels_txt.clicked.connect(self.on_radioButton_labels_txt_clicked)
        self.radioButton_labels_csv.clicked.connect(self.on_radioButton_labels_csv_clicked)
        self.radioButton_data_csv.clicked.connect(self.on_radioButton_data_csv_clicked)
        self.radioButton_data_mysql.clicked.connect(self.on_radioButton_data_mysql_clicked)
        self.radioButton_data_mongodb.clicked.connect(self.on_radioButton_data_mongodb_clicked)
        # 暂时封印未开发的功能
        self.radioButton_labels_csv.setEnabled(False)
        self.radioButton_data_mysql.setEnabled(False)
        self.radioButton_data_mongodb.setEnabled(False)

    def on_pushButton_files_clicked(self):
        self.files_list = []
        self.listWidget_files.clear()
        files_dialog = QtWidgets.QFileDialog()
        files_list, file_type = files_dialog.getOpenFileNames(filter="DTA Files (*.dta)")
        if files_list.__len__() != 0:
            for file in files_list:
                self.files_list.append(file)
                item = QtWidgets.QListWidgetItem()
                file_name = os.path.basename(file)
                item.setText(file_name)
                item.setWhatsThis(file)
                self.listWidget_files.addItem(item)

    def on_pushButton_extract_clicked(self):
        print("---------Extract Start---------")
        print("Labels:\t{0}\n"
              "\tIndex (0-TXT, 1-CSV):\t{1}\n"
              "Data:\t{2}\n"
              "\tIndex (0-CSV, 1-MySQL, 2-MongoDB):\t{3}\n"
              .format(self.labels_flag
                      , self.labels_index
                      , self.data_flag
                      , self.data_index))
        if self.files_list.__len__() == 0:
            QMessageBox(QMessageBox.Warning, 'Warning', 'No files!').exec_()
            return
        if self.labels_flag is False and self.data_flag is False:
            QMessageBox(QMessageBox.Warning, 'Warning', 'Check at least ONE!').exec_()
            return
        else:
            output_path = os.path.dirname(self.files_list[0])
            print("Output Path:{0}".format(output_path))
            # convert_categoricals=False,否则重复的label会报错
            extractor = DTA_Extractor(output_path=output_path,convert_categoricals=False)
            for index in range(self.files_list.__len__()):
                file = self.files_list[index]
                file_name_base = os.path.splitext(os.path.basename(file))[0]
                print("File No.{0}\tName:{1}".format(index, file_name_base))
                # 业务代码开始
                if self.labels_flag is True:
                    if self.labels_index == 0:
                        extractor.extract_labels(file_path=file,file_name_base=file_name_base,to_type=DTA_Extractor.TO_LABELS.TXT)
                    else:
                        print("other labels_index")
                if self.data_flag is True:
                    if self.data_index == 0:
                        extractor.extract_data(file_path=file,file_name_base=file_name_base,to_type=DTA_Extractor.TO_DATA.CSV)
                    else:
                        print("other data_index")
                # 业务代码结束
            QMessageBox(QMessageBox.Information, 'Information', 'Extract over!').exec_()
        print("---------Extract Over---------")

    def on_groupBox_labels_clicked(self):
        self.labels_flag = self.groupBox_labels.isChecked()
        if self.labels_flag:
            self.labels_index = 0
            self.radioButton_labels_txt.setChecked(True)

    def on_groupBox_data_clicked(self):
        self.data_flag = self.groupBox_data.isChecked()
        if self.data_flag:
            self.data_index = 0
            self.radioButton_data_csv.setChecked(True)

    def on_radioButton_labels_txt_clicked(self):
        if self.radioButton_labels_txt.isChecked():
            self.labels_index = 0

    def on_radioButton_labels_csv_clicked(self):
        if self.radioButton_labels_csv.isChecked():
            self.labels_index = 1

    def on_radioButton_data_csv_clicked(self):
        if self.radioButton_data_csv.isChecked():
            self.data_index = 0

    def on_radioButton_data_mysql_clicked(self):
        if self.radioButton_data_mysql.isChecked():
            self.data_index = 1

    def on_radioButton_data_mongodb_clicked(self):
        if self.radioButton_data_mongodb.isChecked():
            self.data_index = 2




class DTA_Extractor():
    class TO_LABELS(Enum):
        TXT = 0
        CSV = 1

    class TO_DATA(Enum):
        CSV = 0
        MYSQL = 1
        MONGODB = 2
    def __init__(self,output_path:str,convert_categoricals:bool):
        self.output_path = output_path
        self.convert_categoricals = convert_categoricals

    def extract_labels(self, file_path: str, file_name_base:str, to_type: TO_LABELS = TO_LABELS.TXT):
        if to_type is DTA_Extractor.TO_LABELS.TXT:
            reader = pd.io.stata.StataReader(file_path,convert_categoricals=self.convert_categoricals)
            data_label = reader.data_label
            value_labels = reader.value_labels()
            variable_labels = reader.variable_labels()
            with open (self.output_path+'/'+file_name_base+'_data_label.txt','w',encoding='utf-8') as f:
                f.write(json.dumps(data_label,indent=4,ensure_ascii=False,cls=DTAEncoder))
            with open (self.output_path+'/'+file_name_base+'_value_labels.txt','w',encoding='utf-8') as f:
                f.write(json.dumps(value_labels,indent=4,ensure_ascii=False,cls=DTAEncoder))
            with open (self.output_path+'/'+file_name_base+'_variable_labels.txt','w',encoding='utf-8') as f:
                f.write(json.dumps(variable_labels,indent=4,ensure_ascii=False,cls=DTAEncoder))
        else:
            print("Error in extract_labels")

    def extract_data(self, file_path: str, file_name_base:str, to_type: TO_DATA = TO_DATA.CSV):
        if to_type is DTA_Extractor.TO_DATA.CSV:
            reader = pd.io.stata.StataReader(file_path,convert_categoricals=self.convert_categoricals)
            reader.read().to_csv(self.output_path+'/'+file_name_base+'_data.csv')
        else:
            print("Error in extract_data")

class DTAEncoder(json.JSONEncoder):
    #一个用来前处理key的类型错误的方法，int32转为int
    def _preprocess(self, obj):
        if isinstance(obj, np.int32):
            return int(obj)
        elif isinstance(obj, dict):
            return {self._preprocess(k): self._preprocess(v) for k,v in obj.items()}
        elif isinstance(obj, list):
            return [self._preprocess(i) for i in obj]
        return obj

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(DTAEncoder, self).default(obj)

    def iterencode(self, obj, _one_shot=True):
        return super().iterencode(self._preprocess(obj), _one_shot=True)

def on_Action_quit():
    sys.exit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    pdf_toolbox = DTA_Toolbox()
    pdf_toolbox.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
