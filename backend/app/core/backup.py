from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.mongo import get_mongo_db

# ============================================
# BACKUP CONFIGURATION
# ============================================

BACKUP_RETENTION_DAYS = 30
BACKUP_COLLECTIONS = [
    "users",
    "chats", 
    "messages",
    "auth_otps",
    "reset_tokens",
    "sessions",
    "audit_logs",
    "agent_tasks",
    "notifications",
]

# ============================================
# S3 CLIENT
# ============================================

def get_s3_client():
    """Get S3 client with credentials from settings"""
    return boto3.client(
        's3',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

# ============================================
# BACKUP FUNCTIONS
# ============================================

async def backup_collection(collection_name: str) -> Dict[str, Any]:
    """Backup a single collection to S3"""
    try:
        db = await get_mongo_db()
        collection = db[collection_name]
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"backups/{collection_name}/{timestamp}.json"
        
        # Get all documents
        documents = []
        async for doc in collection.find():
            doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        if not documents:
            return {
                'collection': collection_name,
                'count': 0,
                'file': file_name,
                'status': 'empty'
            }
        
        # Upload to S3
        s3 = get_s3_client()
        s3.put_object(
            Bucket=settings.AWS_S3_BACKUP_BUCKET,
            Key=file_name,
            Body=json.dumps(documents, default=str),
            ContentType='application/json'
        )
        
        return {
            'collection': collection_name,
            'count': len(documents),
            'file': file_name,
            'timestamp': timestamp,
            'status': 'success'
        }
        
    except ClientError as e:
        return {
            'collection': collection_name,
            'status': 'failed',
            'error': f"AWS Error: {str(e)}"
        }
    except Exception as e:
        return {
            'collection': collection_name,
            'status': 'failed',
            'error': str(e)
        }

async def run_full_backup() -> Dict[str, Any]:
    """Run full database backup"""
    print("🔄 Starting database backup...")
    
    results = []
    total_documents = 0
    
    for collection_name in BACKUP_COLLECTIONS:
        result = await backup_collection(collection_name)
        results.append(result)
        if result.get('status') == 'success':
            total_documents += result.get('count', 0)
            print(f"  ✅ Backed up {collection_name}: {result.get('count', 0)} documents")
        elif result.get('status') == 'empty':
            print(f"  ⚠️ {collection_name}: empty collection")
        else:
            print(f"  ❌ Failed to backup {collection_name}: {result.get('error', 'Unknown error')}")
    
    # Clean old backups
    await cleanup_old_backups()
    
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'collections': results,
        'total_collections': len(results),
        'total_documents': total_documents,
        'status': 'success' if all(r.get('status') in ['success', 'empty'] for r in results) else 'partial'
    }
    
    print(f"✅ Backup completed! Total documents: {total_documents}")
    return summary

async def cleanup_old_backups():
    """Delete backups older than retention period"""
    try:
        s3 = get_s3_client()
        cutoff_date = datetime.utcnow() - timedelta(days=BACKUP_RETENTION_DAYS)
        
        # List all backup objects
        response = s3.list_objects_v2(
            Bucket=settings.AWS_S3_BACKUP_BUCKET,
            Prefix='backups/'
        )
        
        if 'Contents' not in response:
            return
        
        deleted_count = 0
        for obj in response['Contents']:
            key = obj['Key']
            last_modified = obj['LastModified']
            
            if last_modified < cutoff_date:
                s3.delete_object(
                    Bucket=settings.AWS_S3_BACKUP_BUCKET,
                    Key=key
                )
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"  🗑️ Deleted {deleted_count} old backup(s)")
            
    except Exception as e:
        print(f"  ⚠️ Error cleaning up old backups: {e}")

# ============================================
# LIST BACKUPS
# ============================================

async def list_backups(collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available backups for a collection"""
    try:
        s3 = get_s3_client()
        prefix = f"backups/{collection_name}/" if collection_name else "backups/"
        
        response = s3.list_objects_v2(
            Bucket=settings.AWS_S3_BACKUP_BUCKET,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return []
        
        backups = []
        for obj in response['Contents']:
            # Extract collection and timestamp from key
            key_parts = obj['Key'].split('/')
            if len(key_parts) >= 3:
                backups.append({
                    'collection': key_parts[1],
                    'file': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        
        return sorted(backups, key=lambda x: x['last_modified'], reverse=True)
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return []
