import os
import boto3
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_active_user
from app.models.schema import User
from pydantic import BaseModel

class PreSignRequest(BaseModel):
    filename: str
    file_type: str

router = APIRouter()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "spendwise-receipts-default")

# Requires AWS credentials configured via aws configure or environment vars
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION
)

@router.post("/presigned-url")
def generate_presigned_url(request: PreSignRequest, current_user: User = Depends(get_current_active_user)):
    try:
        # Generate a unique object key using employee ID and timestamp to prevent collisions
        import time
        safe_filename = request.filename.replace(" ", "_").lower()
        object_key = f"receipts/user_{current_user.id}/{int(time.time())}_{safe_filename}"
        
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=object_key,
            Fields={"Content-Type": request.file_type},
            Conditions=[
                {"Content-Type": request.file_type},
                ["content-length-range", 1, 10485760] # Allow up to 10MB
            ],
            ExpiresIn=3600 # URL valid for 1 hour
        )
        
        # Build the final URL that will be saved to the database once the upload finishes
        final_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
        
        return {
            "presigned_post": presigned_post,
            "final_url": final_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
