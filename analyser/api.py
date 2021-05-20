import traceback

from fastapi import FastAPI, status
from fastapi.responses import ORJSONResponse

from analyser import models
from analyser.packages import poetry

app = FastAPI()


@app.exception_handler(Exception)
async def http_exception_handler(request, exc):
    return ORJSONResponse(
        {"detail": str(exc), "traceback": traceback.format_tb(exc.__traceback__)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.get("/_/health")
def health():
    return {"status": "healthy"}


@app.get("/_/ready")
def ready():
    return {"status": "ready"}


@app.post("/analysis", response_model=models.AnalysisEcoSystemResult)
async def do_analysis(
    analysis_request: models.PerformAnalysisRequest,
) -> models.AnalysisEcoSystemResult:
    objects = await poetry.objects_from_packages(analysis_request.path)
    return models.AnalysisEcoSystemResult(name="python", objects=objects)
