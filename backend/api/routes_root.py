from fastapi import APIRouter,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Root"])

templates = Jinja2Templates(directory="backend/templates")

@router.get("/",response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request = request , name = "index.html")