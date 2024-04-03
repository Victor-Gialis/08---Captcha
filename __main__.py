__authors__ = ("Victor Gialis")
__contact__ = ("victor.gialis@gmail.com")
__copyright__ = "Université Jean-Monnet"
__date__ = "2024-03-04"
__version__= "1.1"

import os
import sys
import random
import requests
import pandas as pd

from PyQt5.QtWidgets import QApplication,QMenu, QMainWindow, QDialog, QAction, QPushButton, QStatusBar, QLabel, QTableWidgetItem, QTableWidget,QGraphicsView, QGraphicsTextItem, QGraphicsScene, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPen, QFont
from PyQt5 import uic

BUTTON_NAMES = ['Image_1','Image_2']
RESOURCES = 'resources'

class ClickMetrics(QDialog):
    
    def __init__(self):
        
        super(ClickMetrics, self).__init__()
        uic.loadUi(r'Metrics.ui',self)

        self.table_widget = self.findChild(QTableWidget,'tableWidget')
        self.total_label = self.findChild(QLabel,'totalLabel')
        self.valid_label = self.findChild(QLabel,'validLabel')
        self.not_valid_label = self.findChild(QLabel,'notvalidLabel')

        # Chargement du fichier contenant les statistiques
        self.loadCsv()

        self.close_button = self.findChild(QPushButton,'closeButton')
        self.close_button.clicked.connect(self.closeDialog)
    
    def closeDialog(self):
        """Change the image icon of push button

        Args :
            None

        Return :
            None
        """
        self.accept()

    def loadCsv(self)->None:
        """Load the csv file with click statistics

        Args :
            None

        Return :
            None
        """
        filepath = os.path.join(os.getcwd(),'metric','data.csv')
        try:
            df = pd.read_csv(filepath)
            self.displayData(df)
        except Exception as e:
            print("Error loading CSV:", e)

    def displayData(self, data)->None:
        """Display the valid and not valid clicks.
        Display with a pie chart the repartiotion click in terms of the image description.

        Args :
            None

        Return :
            None
        """
        self.table_widget.setRowCount(data.shape[0])
        self.table_widget.setColumnCount(data.shape[1])
        self.table_widget.setHorizontalHeaderLabels(data.columns)

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                item = QTableWidgetItem(str(data.iloc[row, col]))
                self.table_widget.setItem(row, col, item)

        pie_chart = self.findChild(QGraphicsView,'graphicsView')
        scene = QGraphicsScene()
        pie_chart.setScene(scene)

        # On calcul le nombre total de clics sur toutes les images
        total_click = data["Total_click"].sum()

        self.total_label.setText(f'Total click : {total_click}')
        self.valid_label.setText(f'Total valid click : {data["Valid"].sum()}')
        self.not_valid_label.setText(f'Total not valid click : {data["Not_valid"].sum()}')

        # On calcul le nombre total de clics sur toutes les images en fonction des animaux représentés
        descriptions = data['Description'].unique()
        values = [data.loc[data['Description'] == d]['Total_click'].sum() for d in descriptions]

        chars = '0123456789ABCDEF'
        colors = [QColor('#'+''.join(random.sample(chars,6))) for i in range(len(values))]
        start_angle = 0

        # Dessiner chaque portion du pie chart
        for value, color in zip(values, colors):
            # Calculer l'angle de la portion actuelle
            angle = value * 360 / total_click
            print(angle)

            # Créer un arc pour représenter cette portion
            arc = scene.addEllipse(-100, -100, 200, 200, QPen(color), color)
            arc.setStartAngle(int(start_angle) * 16)
            arc.setSpanAngle(int(angle) * 16)

            # Mise à jour de l'angle de départ pour la prochaine portion
            start_angle += angle
        
        # Calcul du pourcentage de cette portion
        percentage = (values/total_click)*100

        # Ajouter une légende
        legend = descriptions  # Exemple de légende
        for i, label in enumerate(legend):
            text = QGraphicsTextItem(f'{label} : {percentage[i]:.1f} %')
            text.setDefaultTextColor(colors[i])
            text.setFont(QFont("Arial", 10))
            text.setPos(150, i * 20)
            scene.addItem(text)

        # Ajouter un titre
        title_text = scene.addText('Pet pictutes - Click repartition', QFont("Arial", 12))
        title_text.setPos(-50, -150)
        
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(r'MainWindow.ui',self)
        
        # Connection des actions pour le menu File
        browse_action = self.findChild(QAction,'Browse')
        browse_action.triggered.connect(self.browseDatabase)

        # Connection des actions pour le menu Edit
        metric_action = self.findChild(QAction,'Metrics')
        metric_action.triggered.connect(self.displaymetricsWindow)

        # Connection du bouton Next pour changer les images
        next_button = self.findChild(QPushButton,'NextButton') 
        next_button.clicked.connect(self.changeImage)

        self.buttons = dict()
        for objectname in BUTTON_NAMES :
            button = self.findChild(QPushButton, objectname)
            button.clicked.connect(self.checkImage) 
            self.buttons[objectname] = button

        # On créer la barre de statuts (de type QStatusBar) avec son message initial
        self.statusBar().showMessage("Label 0 : Initialisation") 

        # On créer le fichier permettant d'enregister les clics
        df = pd.DataFrame(columns=['Url','Description','Total_click','Valid','Not_valid'])
        df.to_csv('metric/data.csv')
    
    # Action qui permet de charger le fichier csv avec les url des images
    def browseDatabase(self)->None:
        """
        It's a class method for load picture url database, like a csv file.
        Browse the csv datafile with url and image description. The file muste have a "Url" and "Descritpion" columns names.

        Args :
            None
        
        Retrun : 
            None
        """
        self.statusBar().showMessage("Label 2 : Browse data file") 
        file_filter = 'Data File (*.csv)'
        response = QFileDialog.getOpenFileName(
            parent = self,
            caption='Select a data file',
            directory=os.getcwd(),
            filter=file_filter,
        )

        self.df = pd.read_csv(response[0],sep=',')
        self.changeImage()

    def setpictureButton(self)->None:
        """
        This method request the image with the url and load the image on the button icon.

        Args :
            None
        
        Return :
            None
        """
        self.statusBar().showMessage("Label 3 : Set pictures") 

        # On sélectionne aléatoirement en fonction de la colonne description du fichier de données
        DESCRIPTIONS = list(self.df['Description'].unique())
        self.descriptions_selected = random.sample(DESCRIPTIONS,2)
        self.true_description = self.descriptions_selected[random.randint(0,1)]

        question_label = self.findChild(QLabel,'questionLabel')
        question_label.setText(f'Where is the {self.true_description} ?')

        self.image_attributions = dict()

        for objectname,description in zip(BUTTON_NAMES,self.descriptions_selected) :
            frame = self.df.loc[self.df['Description']==description]
            row_selected = frame.sample(n=1)

            image_url = row_selected['Url'].values[0]
            self.image_attributions[objectname] = {'Url':image_url,'Description':description,'Nbr_click':0}

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
                self.buttons[objectname].setIcon(icon)

                # Redimensionner le bouton pour qu'il corresponde à la taille de l'image
                self.buttons[objectname].setFixedSize(image_width, image_height)
                self.buttons[objectname].setIconSize(pixmap.rect().size())

        self.statusBar().showMessage("Label 1 : Waiting action") 
    
    def checkImage(self)->None:
        """ It's a class method activate when the user click on a image.
        This method check if the picture match with the captcha question.

        Args :
            None

        Return :
            None
        """
        self.statusBar().showMessage("Label 4 : Check picture") 
        sender = self.sender() # Récupérer le bouton qui a émis le signal
        object_name = sender.objectName()

        # On compte le nombre de clics par image
        self.image_attributions[object_name]['Nbr_click'] += 1

        if self.image_attributions[object_name]['Description'] == self.true_description:
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
        description = self.image_attributions[object_name]['Description']
        self.stroreclickMetric(url,description,validstate)
        self.statusBar().showMessage("Label 1 : Waiting action") 

    def changeImage(self)->None:
        """Change the image icon of push button

        Args :
            None

        Return :
            None
        """
        self.statusBar().showMessage("Label 5 : Next pictures") 
        question_label = self.findChild(QLabel,'validationLabel')
        question_label.setText('')
        self.setpictureButton()
    
    def stroreclickMetric(self,url:str,description:str,validstate:bool)->None:
        """Storage the parameters of the image clicked

        Args :
            url (str) : A url of web image
            description (str) : The word decription of the image
            validstate (bool) : True if the image clicked is the rigth aswer
        Returns :
            None
        """
        filepath = os.path.join(os.getcwd(),'metric','data.csv')
        df = pd.read_csv(filepath)

        if not (df['Url'].eq(url)).any():
            body = {'Url':url,
                    'Description':description,
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
    
    def displaymetricsWindow(self):
        """Display with a button the metrics dashoard

        Args :
            None

        Return :
            None
        """
        self.window = ClickMetrics()
        self.window.show()

    def deletesecondWindow(self):
        """Delete with a button the metrics dashoard

        Args :
            None

        Return :
            None
        """
        self.window.deleteLater()
        self.window = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    captcha = MainWindow()
    captcha.show()
    sys.exit(app.exec_())