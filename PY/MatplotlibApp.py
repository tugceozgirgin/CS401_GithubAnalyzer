import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QPushButton, QHBoxLayout
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from PY.analyzes.graph_algorithms import GraphAlgorithms


class MatplotlibApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.graph = GraphAlgorithms()

        # Set up the main window
        self.setWindowTitle('Matplotlib Plots in PyQt')
        self.setGeometry(100, 100, 1000, 800)

        # Create a central widget and set it as the main widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a stacked widget to manage different pages
        self.stacked_widget = QStackedWidget(central_widget)

        for i in range(10):
            # Create Matplotlib figure and axis
            fig, ax = plt.subplots()

            # Determine which plot method to call based on the index (i)
            if i == 0:
                self.graph.plot_savant(ax)
            elif i == 1:
                self.graph.plot_lines_modified_histogram(ax)
            elif i == 2:
                self.graph.plot_commits_per_developer_histogram(ax)
            elif i == 3:
                self.graph.plot_lines_modified_histogram2(ax)
            elif i == 4:
                self.graph.plot_files_modified_boxplot(ax)
            elif i == 5:
                self.graph.plot_lines_modified_boxplot(ax)



            # Create a FigureCanvas widget for each plot
            canvas = FigureCanvas(fig)

            # Add the FigureCanvas widget to a new page in the stacked widget
            page_widget = QWidget()
            page_layout = QVBoxLayout(page_widget)
            page_layout.addWidget(canvas)

            # Add navigation buttons and zoom button to the page
            nav_toolbar = NavigationToolbar(canvas, self)

            # Add buttons and canvas to the layout
            page_layout.addWidget(nav_toolbar)
            self.stacked_widget.addWidget(page_widget)

        # Set up the central layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

        # Add navigation buttons to switch between pages
        nav_layout = QHBoxLayout()
        prev_button = QPushButton('Previous Page', self)
        prev_button.clicked.connect(self.prev_page)
        next_button = QPushButton('Next Page', self)
        next_button.clicked.connect(self.next_page)
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(next_button)
        layout.addLayout(nav_layout)

        # Initial page index
        self.current_page = 0

    def on_plot_clicked(self, event, idx):
        # Double the size of the clicked plot
        width, height = self.figs[idx][0].get_size_inches()
        self.figs[idx][0].set_size_inches(2 * width, 2 * height)
        self.figs[idx][0].canvas.draw()

    def toggle_zoom(self, idx):
        # Toggle between normal and double-sized views for the selected page
        width, height = self.figs[idx][0].get_size_inches()
        if width == 2 and height == 2:
            self.figs[idx][0].set_size_inches(1, 1)
        else:
            self.figs[idx][0].set_size_inches(2, 2)
        self.figs[idx][0].canvas.draw()

    def prev_page(self):
        # Switch to the previous page
        self.current_page = (self.current_page - 1) % self.stacked_widget.count()
        self.stacked_widget.setCurrentIndex(self.current_page)

    def next_page(self):
        # Switch to the next page
        self.current_page = (self.current_page + 1) % self.stacked_widget.count()
        self.stacked_widget.setCurrentIndex(self.current_page)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MatplotlibApp()
    window.show()
    sys.exit(app.exec_())
