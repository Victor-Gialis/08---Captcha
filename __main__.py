import os
import sys
import random
import requests
import pandas as pd

from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QLabel, QTableWidgetItem, QTableWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import uic

BUTTONNAMES = ['Image_1','Image_2']
PET = ['Dog','Cat']
RESOURCES = 'resources'

class ClickMetrics(QDialog):
    
    def __init__(self):
        super(ClickMetrics, self).__init__()
        uic.loadUi(r'C:\\Users\\v.gialis\\OneDrive - pellencst.com\\Documents\\internship\\Alternance\\03_M2_T3I\\06 - Projet\\08 - Captcha\\Metrics.ui',self)

        self.table_widget = self.findChild(QTableWidget,'tableWidget')
        self.load_csv()

    def load_csv(self):
        filepath = os.path.join(os.getcwd(),'metric','data.csv')
        try:
            df = pd.read_csv(filepath)
            self.display_data(df)
        except Exception as e:
            print("Error loading CSV:", e)

    def display_data(self, data):
        self.table_widget.setRowCount(data.shape[0])
        self.table_widget.setColumnCount(data.shape[1])
        self.table_widget.setHorizontalHeaderLabels(data.columns)

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                item = QTableWidgetItem(str(data.iloc[row, col]))
                self.table_widget.setItem(row, col, item)

class Captcha(QDialog):

    def __init__(self):
        super(Captcha, self).__init__()
        uic.loadUi(r'C:\\Users\\v.gialis\\OneDrive - pellencst.com\\Documents\\internship\\Alternance\\03_M2_T3I\\06 - Projet\\08 - Captcha\\Captcha.ui',self)

        self.window = None
        # Initialisation des images
        self.set_picture_button()

        # Connection du bouton Next à son Event
        button_next = self.findChild(QPushButton,'nextImage')
        button_next.clicked.connect(self.change_image)

        # Connection du bouton Click Metrics à son Event
        button_metric = self.findChild(QPushButton,'clickMetrics')
        button_metric.clicked.connect(self.display_metrics_window)

    def set_picture_button(self):
        # On sélectionne aléatoirement le chien ou le chat
        self.pet_selected = PET[random.randint(0,1)]

        question_label = self.findChild(QLabel,'questionLabel')
        question_label.setText(f'Where is the {self.pet_selected} ?')

        random.shuffle(PET)
        self.image_attributions = dict()

        for objectName,pet in zip(BUTTONNAMES,PET) :
            df = pd.read_csv(os.path.join(os.getcwd(),RESOURCES,pet+'.csv')) # Chargement du tableur excel contenant les url des images
            image_url = df.sample().values[0][0] # Sélection aléatoire d'un url

            self.image_attributions[objectName] = {'Url':image_url,'Pet':pet,'Nbr_click':0}

            button = self.findChild(QPushButton, objectName)
            button.clicked.connect(self.check_image)       

            # Télécharger l'image depuis l'URL
            response = requests.get(image_url)

            if response.status_code == 200:
                # Convertir la réponse en pixmap
                image_data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)

                # Redimensionner l'image à la taille souhaitée
                image_width = 245
                image_height = 245
                pixmap = pixmap.scaled(image_width, image_height)

                # Changer l'icône du bouton existant
                icon = QIcon(pixmap)

                # Changer l'icône du bouton existant
                button.setIcon(icon)

                # Redimensionner le bouton pour qu'il corresponde à la taille de l'image
                button.setFixedSize(image_width, image_height)
                button.setIconSize(pixmap.rect().size())
    
    def check_image(self):
        sender = self.sender() # Récupérer le bouton qui a émis le signal
        object_name = sender.objectName()

        # On compte le nombre de clics par image
        self.image_attributions[object_name]['Nbr_click'] += 1

        if self.image_attributions[object_name]['Pet'] == self.pet_selected :
            print('click validate')
            validstate = True
            validationtext = 'Good job ! You find the good one !'

        else :
            print('click not validate')
            validstate = False
            validationtext = 'Please retry again ! No pain, no gain !'

        question_label = self.findChild(QLabel,'validationLabel')
        question_label.setText(validationtext)

        url =self.image_attributions[object_name]['Url']
        pet = self.image_attributions[object_name]['Pet']
        self.strore_click_metric(url,pet,validstate)

    def change_image(self):
        question_label = self.findChild(QLabel,'validationLabel')
        question_label.setText('')

        self.set_picture_button()
    
    def strore_click_metric(self,url:str,pet:str,validstate:bool):
        filepath = os.path.join(os.getcwd(),'metric','data.csv')
        df = pd.read_csv(filepath)

        if not (df['Url'].eq(url)).any():
            body = {'Url':url,
                    'Pet':pet,
                    'Total_click':[0],
                    'Valid':[0],
                    'Not_valid':[0]
                    }
            body = pd.DataFrame(body)
            df = pd.concat([df,body])
        
        else :
            index = list(df.loc[df['Url'] == url].index)
            df.loc[index[0],'Total_click'] = df.loc[index[0],'Total_click'] + 1

            if validstate :
                df.loc[index[0],'Valid'] = df.loc[index[0],'Valid'] + 1

            else :
                df.loc[index[0],'Not_valid'] = df.loc[index[0],'Not_valid'] + 1
        
        df.to_csv(filepath,index=False)
    
    def display_metrics_window(self):
        if self.window is None:
            self.window = ClickMetrics()
        self.window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    captcha = Captcha()
    captcha.show()
    sys.exit(captcha.exec_())