from fastapi import APIRouter,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,RedirectResponse
from backend.core.dependencies import get_current_user
from backend.logging_fastapi.logger_api import auth_logger

router = APIRouter(tags=["Root"])

templates = Jinja2Templates(directory="backend/templates")

@router.get("/",response_class=HTMLResponse)
def root(request: Request):
    try:
        user_id = get_current_user(request)
    except Exception as e :
        auth_logger.save_logs(f"Issue Occured while accessing home page : {str(e)}",log_level="error")
        return RedirectResponse(
            url = "/auth/login",
            status_code=303
        )
    auth_logger.save_logs("Login Successfull Users can now see index page")
    return templates.TemplateResponse(
        request=request,
        name = "index.html",
        context={"user_id" : user_id}
    )

