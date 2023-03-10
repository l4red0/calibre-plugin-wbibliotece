#!/usr/bin/env python3
from __future__ import (unicode_literals, division, absolute_import, print_function)
from calibre.utils.config import JSONConfig
from PyQt5.Qt import QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QGroupBox, \
    QLabel, QLineEdit, QIntValidator, QDoubleValidator, QCheckBox, QTabWidget
from PyQt5.QtWidgets import QSizePolicy

__license__ = 'MIT'
__copyright__ = '2023 l4red0'
__docformat__ = 'restructuredtext en'


IDENTIFIER = 'wbibliotece'

URL_SCHEME_TITLE = 'https://w.bibliotece.pl/search/?q=t%3A{title}'
URL_SCHEME_TITLE_AUTHORS = 'https://w.bibliotece.pl/search/?q=o%3A{authors}+t%3A{title}'
URL_SCHEME_ISBN = 'https://w.bibliotece.pl/search/?q=isbn%3A+{isbn}'

AUTHORS_JOIN_DELIMETER = '+'
AUTHORS_SPLIT_DELIMETER = '+'
SKIP_AUTHORS = ('Unknown', 'Nieznany')

prefs = JSONConfig('plugins/{}'.format(IDENTIFIER))

prefs.defaults['max_results'] = 2
prefs.defaults['authors_search'] = True
prefs.defaults['only_first_author'] = False
prefs.defaults['covers'] = True
prefs.defaults['max_covers'] = 5
prefs.defaults['threads'] = True
prefs.defaults['max_threads'] = 3
prefs.defaults['thread_delay'] = 0.1
prefs.defaults['metamover'] = False

# metadata settings
prefs.defaults['title'] = True
prefs.defaults['authors'] = True
prefs.defaults['pubdate'] = True
prefs.defaults['publisher'] = True
prefs.defaults['series'] = True
prefs.defaults['isbn'] = True
prefs.defaults['comments'] = True
prefs.defaults['languages'] = True
prefs.defaults['rating'] = True
prefs.defaults['tags'] = True
prefs.defaults['identifier'] = True

# additional metadata (metamover)
#prefs.defaults['metamoverenabled'] = False
#prefs.defaults['translators'] = False


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.main_layout = QVBoxLayout()
        self.group_box = QGroupBox('')
        self.group_box2 = QGroupBox('')
        self.l0 = QFormLayout()
        self.l2 = QVBoxLayout()

        # Create a QTabWidget
        tabs = QTabWidget()

        # Create the tabs and add the group boxes to them
        tab1 = QWidget()
        tab2 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab2_layout = QVBoxLayout(tab2)

        tab1_layout.addWidget(self.group_box)
        tab2_layout.addWidget(self.group_box2)

        # Add the tabs to the QTabWidget
        tabs.addTab(tab1, "Ustawienia og??lne")
        tabs.addTab(tab2, "Rodzaj metadanych")
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # add the tabs to main layout
        self.main_layout.addWidget(tabs)

        # general settings
        self.max_results_label = QLabel('Maksymalna liczba wynik??w')
        self.max_results_label.setToolTip('Maksymalna liczba pobieranych metadanych. Dla ksi????ek o nieunikalnych tytu??ach \
pierwszy wynik mo??e by?? niepoprawny')
        self.max_results = QLineEdit(self)
        self.max_results.setValidator(QIntValidator())
        self.max_results.setText(str(prefs['max_results']))
        self.max_results_label.setBuddy(self.max_results)
        self.l0.addRow(self.max_results_label, self.max_results)

        self.authors_search_label = QLabel('U??ywaj autor??w do wyszukiwa??')
        self.authors_search_label.setToolTip('Wyszukuj uwzgl??dniaj??c autor??w. Mo??e poprawi?? trafno???? wynik??w, ale b????dni autorzy spowoduj?? brak wynik??w')
        self.authors_search = QCheckBox()
        self.authors_search.setChecked(prefs['authors_search'])
        self.authors_search_label.setBuddy(self.authors_search)
        self.l0.addRow(self.authors_search_label, self.authors_search)

        self.only_first_author_label = QLabel('U??ywaj tylko pierwszego autora do wyszukiwania')
        self.only_first_author_label.setToolTip('U??ywaj tylko pierwszego autora do wyszukiwa??, obowi??zuje tylko gdy wyszukiwanie z autorami jest aktywowane')
        self.only_first_author = QCheckBox()
        self.only_first_author.setChecked(prefs['only_first_author'])
        self.only_first_author_label.setBuddy(self.only_first_author)
        self.l0.addRow(self.only_first_author_label, self.only_first_author)

        self.covers_label = QLabel('Pobieraj ok??adki')
        self.covers = QCheckBox()
        self.covers.setChecked(prefs['covers'])
        self.covers_label.setBuddy(self.covers)
        self.l0.addRow(self.covers_label, self.covers)

        self.max_covers_label = QLabel('Maksymalna liczba ok??adek')
        self.max_covers_label.setToolTip('Maksymalna liczba pobieranych ok??adek')
        self.max_covers = QLineEdit(self)
        self.max_covers.setValidator(QIntValidator())
        self.max_covers.setText(str(prefs['max_covers']))
        self.max_covers_label.setBuddy(self.max_covers)
        self.l0.addRow(self.max_covers_label, self.max_covers)

        self.threads_label = QLabel('Wielow??tkowe przetwarzanie')
        self.threads_label.setToolTip('Przy??piesza prac?? u??ywaj??c wielu w??tk??w')
        self.threads = QCheckBox()
        self.threads.setChecked(prefs['threads'])
        self.threads_label.setBuddy(self.threads)
        self.l0.addRow(self.threads_label, self.threads)

        self.max_threads_label = QLabel('Maksymalna liczba w??tk??w')
        self.max_threads = QLineEdit(self)
        self.max_threads.setValidator(QIntValidator())
        self.max_threads.setText(str(prefs['max_threads']))
        self.max_threads_label.setBuddy(self.max_threads)
        self.l0.addRow(self.max_threads_label, self.max_threads)

        self.thread_delay_label = QLabel('Op????nienie w??tku')
        self.thread_delay_label.setToolTip('Czas oczekiwania na uruchomienie kolejnego w??tku')
        self.thread_delay = QLineEdit(self)
        self.thread_delay.setValidator(QDoubleValidator())
        self.thread_delay.setText(str(prefs['thread_delay']))
        self.thread_delay_label.setBuddy(self.thread_delay)
        self.l0.addRow(self.thread_delay_label, self.thread_delay)

     # metadata settings
        self.title = QCheckBox('Tytu??')
        self.title.setChecked(prefs['title'])
        self.l2.addWidget(self.title)

        self.authors = QCheckBox('Autorzy')
        self.authors.setChecked(prefs['authors'])
        self.l2.addWidget(self.authors)

        self.pubdate = QCheckBox('Data wydania')
        self.pubdate.setChecked(prefs['pubdate'])
        self.l2.addWidget(self.pubdate)

        self.series = QCheckBox('Serie')
        self.series.setChecked(prefs['series'])
        self.l2.addWidget(self.series)

        self.publisher = QCheckBox('Wydawca')
        self.publisher.setChecked(prefs['publisher'])
        self.l2.addWidget(self.publisher)

        self.isbn = QCheckBox('ISBN')
        self.isbn.setChecked(prefs['isbn'])
        self.l2.addWidget(self.isbn)

        self.comments = QCheckBox('Opis')
        self.comments.setChecked(prefs['comments'])
        self.l2.addWidget(self.comments)

        self.languages = QCheckBox('J??zyki')
        self.languages.setChecked(prefs['languages'])
        self.l2.addWidget(self.languages)

        self.rating = QCheckBox('Ocena')
        self.rating.setChecked(prefs['rating'])
        self.l2.addWidget(self.rating)

        self.tags = QCheckBox('Etykiety (tagi)')
        self.tags.setChecked(prefs['tags'])
        self.l2.addWidget(self.tags)

        self.identifier = QCheckBox('Identyfikator')
        self.identifier.setChecked(prefs['identifier'])
        self.l2.addWidget(self.identifier)

        #self.identifier = QCheckBox('Enable metaMOVER')
        #self.identifier.setChecked(prefs['metamoverenabled'])
        #self.l2.addWidget(self.metamoverenabled)

        #self.identifier = QCheckBox('T??umacze')
        #self.identifier.setChecked(prefs['translators'])
        #self.l2.addWidget(self.translators)

        self.group_box.setLayout(self.l0)
        self.group_box2.setLayout(self.l2)
        self.setLayout(self.main_layout)

    def save_settings(self):
        prefs['max_results'] = int(self.max_results.text())
        prefs['authors_search'] = self.authors_search.isChecked()
        prefs['only_first_author'] = self.only_first_author.isChecked()
        prefs['covers'] = self.covers.isChecked()
        prefs['max_covers'] = int(self.max_covers.text())
        prefs['threads'] = self.threads.isChecked()
        prefs['max_threads'] = int(self.max_threads.text())
        prefs['thread_delay'] = float(self.thread_delay.text().replace(',', '.'))

        # metadata settings
        prefs['title'] = self.title.isChecked()
        prefs['authors'] = self.authors.isChecked()
        prefs['pubdate'] = self.pubdate.isChecked()
        prefs['publisher'] = self.publisher.isChecked()
        prefs['series'] = self.series.isChecked()
        prefs['isbn'] = self.isbn.isChecked()
        prefs['comments'] = self.comments.isChecked()
        prefs['languages'] = self.languages.isChecked()
        prefs['rating'] = self.rating.isChecked()
        prefs['tags'] = self.tags.isChecked()
        prefs['identifier'] = self.identifier.isChecked()

        # extended metadata (METAmove)
        #prefs['metamoverenabled'] = self.metamoverenabled.isChecked()
        #prefs['translators'] = self.translators.isChecked()

        return prefs
