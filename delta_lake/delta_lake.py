# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DeltaLake
                                 A QGIS plugin
 With this plugin you can load data from delta lakes
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-12-29
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Richard Kooijman
        email                : kooijman.richard@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from functools import partial
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, QgsProviderRegistry, QgsProject, QgsVectorLayer

# Initialize Qt resources from file resources.py
from .resources import qInitResources
from .provider.toolbelt.log_handler import PluginLogger

# Import the code for the dialog
from .delta_lake_dialog import DeltaLakeDialog
from .provider.delta_lake_metadata import DeltaLakeProviderMetadata
from .provider.delta_lake_provider import DeltaLakeProvider

from .__about__ import (
        __uri_homepage__,
        )


class DeltaLake:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.dlg = None
        self.help_action = None
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Delta Lake')

        register_delta_lake_provider()

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DeltaLake', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/delta_lake/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Delta Lake'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        self.help_action = QAction(
            QgsApplication.getThemeIcon("mActionHelpContents.svg"),
            self.tr("Delta Lake Help"),
            self.iface.mainWindow()
        )
        # Add the action to the Help menu
        self.iface.pluginHelpMenu().addAction(self.help_action)
        self.help_action.triggered.connect(partial(QDesktopServices.openUrl, QUrl(__uri_homepage__)))

    def unload(self):
        self.iface.pluginHelpMenu().removeAction(self.help_action)
        del self.help_action

        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&DeltaLake'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start:
            self.first_start = False
            self.dlg = DeltaLakeDialog()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            delta_lake_provider_metadata = QgsProviderRegistry.instance().providerMetadata(
                DeltaLakeProvider.providerKey()
            )
            uri = delta_lake_provider_metadata.encodeUriFromValues(self.dlg.connection_profile_path,
                                                                   self.dlg.share_name,
                                                                   self.dlg.schema_name,
                                                                   self.dlg.table_name,
                                                                   int(self.dlg.epsg_id))
            layer = QgsVectorLayer(uri, DeltaLakeProvider.layer_name(self.dlg.share_name,
                                                                     self.dlg.schema_name,
                                                                     self.dlg.table_name),
                                   DeltaLakeProvider.providerKey())
            QgsProject.instance().addMapLayer(layer)


def register_delta_lake_provider() -> None:
    """Register delta_lake provider.
    This only needs to be called once.

    :returns: None
    """
    registry = QgsProviderRegistry.instance()
    provider_metadata = DeltaLakeProviderMetadata()
    registry.registerProvider(provider_metadata)

    QgsProject.instance().layersWillBeRemoved.connect(_on_layers_removal)


def _on_layers_removal(layer_ids: list[str]) -> None:
    """Disconnect delta sharing on provider removal

    :param list[str] layer_ids: list of removed layer ids
    """
    # This ensures to disconnect when a
    # layer with a provider is removed.
    for layer_id in layer_ids:
        layer = QgsProject.instance().mapLayer(layer_id)
        provider = layer.dataProvider()
        if provider and provider.name() == DeltaLakeProvider.providerKey():
            provider.disconnect_database()
