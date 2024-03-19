from qgis.core import (
    QgsAbstractFeatureSource,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsProject,
    QgsFeatureIterator
)


from .delta_lake_feature_iterator import DeltaLakeFeatureIterator


class DeltaLakeFeatureSource(QgsAbstractFeatureSource):
    def __init__(self, provider):
        """Constructor"""
        super().__init__()
        self._provider = provider

        self._expression_context = QgsExpressionContext()
        self._expression_context.appendScope(QgsExpressionContextUtils.globalScope())
        self._expression_context.appendScope(
            QgsExpressionContextUtils.projectScope(QgsProject.instance())
        )
        self._expression_context.setFields(self._provider.fields())
        if self._provider.subsetString():
            self._subset_expression = QgsExpression(self._provider.subsetString())
            self._subset_expression.prepare(self._expression_context)
        else:
            self._subset_expression = None

    def getFeatures(self, request):
        return QgsFeatureIterator(
            DeltaLakeFeatureIterator(self, request)
        )

    def get_provider(self):
        return self._provider
