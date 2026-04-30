[33mcommit 8ed36a5ae03a008734b1252b9fab418277299df6[m[33m ([m[1;36mHEAD -> [m[1;32mmodel-eval-avi[m[33m, [m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: Avanindra Bose <avanindrabose0218@gmail.com>
Date:   Thu Apr 30 06:37:21 2026 +0530

    Testing CI Workflow by minor changes in Pipeline

[1mdiff --git a/src/models/model_evaluation.py b/src/models/model_evaluation.py[m
[1mindex ae753ad..318c6c5 100644[m
[1m--- a/src/models/model_evaluation.py[m
[1m+++ b/src/models/model_evaluation.py[m
[36m@@ -104,9 +104,13 @@[m [mdef evaluate_model(clf, X_test: np.ndarray, y_test: np.ndarray) -> dict:[m
             'recall': recall,[m
             'auc': auc[m
         }[m
[32m+[m
         logger.debug('Model evaluation metrics calculated')[m
[32m+[m
         evaluation_logger.save_logs(f"Model evaluation metrics calculated: {metrics_dict}", log_level='info')[m
[32m+[m
         return metrics_dict[m
[32m+[m[41m    [m
     except Exception as e:[m
         logger.error('Error during model evaluation: %s', e)[m
         evaluation_logger.save_logs(f"Error during model evaluation: {e}", log_level='error')[m
