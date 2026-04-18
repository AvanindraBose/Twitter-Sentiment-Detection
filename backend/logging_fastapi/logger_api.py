from src.logger_class import CustomLogger,create_log_path

prediction_logger = CustomLogger(
    logger_name="prediction",
    log_filename=create_log_path("Prediction")
)

auth_logger = CustomLogger(
    logger_name="auth",
    log_filename=create_log_path("Auth")
)

health_logger = CustomLogger(
    logger_name="health",
    log_filename=create_log_path("Health")
)