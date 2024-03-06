import os
import sys
import random
import requests
import pandas as pd

from PyQt5.QtWidgets import QApplication,QMenu, QMainWindow, QDialog, QAction, QPushButton, QStatusBar, QLabel, QTableWidgetItem, QTableWidget,QGraphicsView, QGraphicsTextItem, QGraphicsScene, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPen, QFont
from PyQt5 import uic

BUTTONNAMES = ['Image_1','Image_2']
PET = ['Dog','Cat']
RESOURCES = 'resources'

class ClickMetrics(QDialog):
    
    def __init__(self):
        super(ClickMetrics, self).__init__()
        uic.loadUi(r'Metrics.ui',self)

        self.table_widget = self.findChild(QTableWidget,'tableWidget')
        self.total_label = self.findChild(QLabel,'totalLabel')
        self.valid_label = self.findChild(QLabel,'validLabel')
        self.not_valid_label = self.findChild(QLabel,'notvalidLabel')

        self.load_csv()

        self.close_button = self.findChild(QPushButton,'closeButton')
        self.close_button.clicked.connect(self.closeDialog)
    
    def closeDialog(self):
        self.accept()

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

        pie_chart = self.findChild(QGraphicsView,'graphicsView')
        scene = QGraphicsScene()
        pie_chart.setScene(scene)

        # On calcul le nombre total de clics sur toutes les images
        total_click = data["Total_click"].sum()

        self.total_label.setText(f'Total click : {total_click}')
        self.valid_label.setText(f'Total valid click : {data["Valid"].sum()}')
        self.not_valid_label.setText(f'Total not valid click : {data["Not_valid"].sum()}')

        # On calcul le nombre total de clics sur toutes les images en fonction des animaux représentés
        total_dog_click = data.loc[data['Pet'] == 'Dog']['Total_click'].sum()
        total_cat_click = data.loc[data['Pet'] == 'Cat']['Total_click'].sum()

        values = [total_dog_click,total_cat_click]
        colors = [QColor("#A8ACE1"), QColor("#4F59EA")]
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
        legend = ["Dog", "Cat"]  # Exemple de légende
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
        self.df = None

        # Connection des actions pour le menu File
        browse_action = self.findChild(QAction,'Browse')
        browse_action.triggered.connect(self.browse)

        next_action = self.findChild(QAction,'Next') 
        next_action.triggered.connect(self.change_image)

        # Connection des actions pour le menu Edit
        metric_action = self.findChild(QAction,'Metrics')
        metric_action.triggered.connect(self.display_metrics_window)

        # Connection du bouton Next pour changer les images
        next_button = self.findChild(QPushButton,'NextButton') 
        next_button.clicked.connect(self.change_image)

        # On créé la barre de statuts (de type QStatusBar) avec son message initial
        self.statusBar().showMessage("Label 0 : Initialisation") 
    
    # Action qui permet de charger le fichier csv avec les url des images
    def browse(self):
        self.statusBar().showMessage("Label 2 : Browse data file") 
        file_filter = 'Data File (*.xlsx *.csv)'
        response = QFileDialog.getOpenFileName(
            parent = self,
            caption='Select a data file',
            directory=os.getcwd(),
            filter=file_filter,
        )
        self.df = pd.read_csv(response[0],sep=';')
        self.change_image()

    def set_picture_button(self):
        self.statusBar().showMessage("Label 3 : Set pictures") 
        # On sélectionne aléatoirement en fonction de la colonne description du fichier de données
        DESCRIPTIONS = list(self.df['Description'].unique())
        self.descriptions_selected = random.sample(DESCRIPTIONS,2)
        self.true_description = self.descriptions_selected[random.randint(0,1)]

        question_label = self.findChild(QLabel,'questionLabel')
        question_label.setText(f'Where is the {self.true_description} ?')

        self.image_attributions = dict()

        for objectName,description in zip(BUTTONNAMES,self.descriptions_selected) :
            frame = self.df.loc[self.df['Description']==description]
            row_selected = frame.sample(n=1)

            image_url = row_selected['Url'].values[0]
            self.image_attributions[objectName] = {'Url':image_url,'Description':description,'Nbr_click':0}

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
        self.statusBar().showMessage("Label 1 : Waiting action") 
    
    def check_image(self):
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
        self.strore_click_metric(url,description,validstate)
        self.statusBar().showMessage("Label 1 : Waiting action") 

    def change_image(self):
        self.statusBar().showMessage("Label 5 : Next pictures") 
        question_label = self.findChild(QLabel,'validationLabel')
        question_label.setText('')
        self.set_picture_button()
    
    def strore_click_metric(self,url:str,description:str,validstate:bool):
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
    
    def display_metrics_window(self):
        if self.window is None:
            self.window = ClickMetrics()
            self.window.finished.connect(self.deleteSecondWindow)
            self.window.show()

    def deleteSecondWindow(self):
        self.window.deleteLater()
        self.window = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    captcha = MainWindow()
    captcha.show()
    sys.exit(app.exec_())