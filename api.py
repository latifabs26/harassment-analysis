from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import re
import logging
from datetime import datetime
import os
from pymongo import MongoClient
from detoxify import Detoxify
import pandas as pd

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modèles Pydantic
class SocialPost(BaseModel):
    id: str
    text: str
    author_id: str
    created_at: str
    likes: int
    retweets: int
    replies: int
    url: str
    collected_at: str

class CleanedPost(BaseModel):
    id: str
    original_text: str
    cleaned_text: str
    author_id: str
    created_at: str
    likes: int
    retweets: int
    replies: int
    url: str
    collected_at: str
    processed_at: str

class ToxicityAnalysis(BaseModel):
    id: str
    text: str
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_attack: float
    is_toxic: bool
    confidence_level: str

class ProcessingStatus(BaseModel):
    status: str
    message: str
    processed_count: int
    total_count: int

# Configuration MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = "harassment_analysis"

class DatabaseManager:
    """Gestionnaire de base de données MongoDB"""
    
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URL)
            self.db = self.client[DB_NAME]
            self.posts_collection = self.db["posts"]
            self.analysis_collection = self.db["toxicity_analysis"]
            logger.info("✅ Connexion MongoDB établie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB: {e}")
            raise
    
    def save_post(self, post_data: dict):
        """Sauvegarder un post dans MongoDB"""
        try:
            # Vérifier si le post existe déjà
            existing = self.posts_collection.find_one({"id": post_data["id"]})
            if existing:
                logger.info(f"Post {post_data['id']} déjà existant, mise à jour")
                self.posts_collection.update_one(
                    {"id": post_data["id"]}, 
                    {"$set": post_data}
                )
            else:
                self.posts_collection.insert_one(post_data)
                logger.info(f"✅ Post {post_data['id']} sauvegardé")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde post: {e}")
            raise
    
    def save_analysis(self, analysis_data: dict):
        """Sauvegarder une analyse de toxicité"""
        try:
            # Vérifier si l'analyse existe déjà
            existing = self.analysis_collection.find_one({"id": analysis_data["id"]})
            if existing:
                self.analysis_collection.update_one(
                    {"id": analysis_data["id"]}, 
                    {"$set": analysis_data}
                )
            else:
                self.analysis_collection.insert_one(analysis_data)
                logger.info(f"✅ Analyse {analysis_data['id']} sauvegardée")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde analyse: {e}")
            raise
    
    def get_posts(self, limit: int = 100):
        """Récupérer les posts de la base"""
        try:
            posts = list(self.posts_collection.find({}, {"_id": 0}).limit(limit))
            return posts
        except Exception as e:
            logger.error(f"❌ Erreur récupération posts: {e}")
            return []
    
    def get_analysis(self, limit: int = 100):
        """Récupérer les analyses de toxicité"""
        try:
            analyses = list(self.analysis_collection.find({}, {"_id": 0}).limit(limit))
            return analyses
        except Exception as e:
            logger.error(f"❌ Erreur récupération analyses: {e}")
            return []

class TextCleaner:
    """Nettoyeur de texte pour les posts"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Nettoie le texte des posts"""
        if not text:
            return ""
        
        # Supprimer les URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Supprimer les mentions (@username)
        text = re.sub(r'@\w+', '', text)
        
        # Supprimer les hashtags mais garder le texte
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Supprimer les caractères spéciaux en excès
        text = re.sub(r'[^\w\s\.\!\?\,\:\;\-]', '', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en début/fin
        text = text.strip()
        
        return text

class ToxicityAnalyzer:
    """Analyseur de toxicité utilisant Detoxify"""
    
    def __init__(self):
        try:
            # Charger le modèle Detoxify
            self.model = Detoxify('multilingual')
            logger.info("✅ Modèle Detoxify chargé")
        except Exception as e:
            logger.error(f"❌ Erreur chargement Detoxify: {e}")
            raise
    
    def analyze_toxicity(self, text: str) -> Dict:
        """Analyse la toxicité d'un texte"""
        try:
            # Analyser avec Detoxify
            results = self.model.predict(text)
            
            # Déterminer si le texte est toxique (seuil: 0.7)
            is_toxic = bool(results['toxicity'] > 0.7)
            
            # Déterminer le niveau de confiance
            max_score = max(results.values())
            if max_score > 0.8:
                confidence = "high"
            elif max_score > 0.5:
                confidence = "medium"
            else:
                confidence = "low"
            
            analysis = {
                'toxicity': float(results['toxicity']),
                'severe_toxicity': float(results['severe_toxicity']),
                'obscene': float(results['obscene']),
                'threat': float(results['threat']),
                'insult': float(results['insult']),
                'identity_attack': float(results['identity_attack']),
                'is_toxic': is_toxic,
                'confidence_level': confidence
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse toxicité: {e}")
            # Retourner des valeurs par défaut en cas d'erreur
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0,
                'is_toxic': False,
                'confidence_level': 'error'
            }

# Initialisation
app = FastAPI(
    title="API d'Analyse de Harcèlement",
    description="API pour nettoyer, analyser la toxicité et stocker les posts sur le harcèlement",
    version="1.0.0"
)

db_manager = DatabaseManager()
text_cleaner = TextCleaner()
toxicity_analyzer = ToxicityAnalyzer()

# Routes API

@app.get("/")
async def root():
    """Route de base"""
    return {
        "message": "API d'Analyse de Harcèlement",
        "version": "1.0.0",
        "endpoints": [
            "/upload-posts",
            "/clean-text",
            "/analyze-toxicity",
            "/process-file",
            "/get-posts",
            "/get-analysis",
            "/stats"
        ]
    }

@app.post("/upload-posts")
async def upload_posts(posts: List[SocialPost]):
    """Upload des posts vers la base de données"""
    try:
        processed = 0
        for post in posts:
            post_data = post.dict()
            db_manager.save_post(post_data)
            processed += 1
        
        return {
            "status": "success",
            "message": f"{processed} posts sauvegardés",
            "count": processed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")

@app.post("/clean-text")
async def clean_text_endpoint(text: str):
    """Nettoie un texte"""
    try:
        cleaned = text_cleaner.clean_text(text)
        return {
            "original": text,
            "cleaned": cleaned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

@app.post("/analyze-toxicity")
async def analyze_toxicity_endpoint(text: str):
    """Analyse la toxicité d'un texte"""
    try:
        analysis = toxicity_analyzer.analyze_toxicity(text)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")

@app.post("/process-file")
async def process_file(background_tasks: BackgroundTasks):
    """Traite le fichier JSON des posts collectés"""
    try:
        # Vérifier si le fichier existe
        file_path = "harassment_posts.json"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Fichier harassment_posts.json non trouvé")
        
        # Lancer le traitement en arrière-plan
        background_tasks.add_task(process_posts_background, file_path)
        
        return {
            "status": "processing",
            "message": "Traitement démarré en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur traitement: {str(e)}")

async def process_posts_background(file_path: str):
    """Traite les posts en arrière-plan"""
    try:
        # Charger les posts
        with open(file_path, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        processed = 0
        total = len(posts_data)
        logger.info(f"🚀 Début traitement de {total} posts")
        
        for post_data in posts_data:
            # Nettoyer le texte
            cleaned_text = text_cleaner.clean_text(post_data['text'])
            
            # Analyser la toxicité
            toxicity_analysis = toxicity_analyzer.analyze_toxicity(cleaned_text)
            
            # Préparer les données pour la base
            post_record = {
                **post_data,
                'cleaned_text': cleaned_text,
                'processed_at': datetime.now().isoformat()
            }
            
            analysis_record = {
                'id': post_data['id'],
                'text': cleaned_text,
                'analyzed_at': datetime.now().isoformat(),
                **toxicity_analysis
            }
            
            # Sauvegarder en base
            db_manager.save_post(post_record)
            db_manager.save_analysis(analysis_record)
            
            processed += 1
            if processed % 10 == 0:
                logger.info(f"📊 Traité: {processed}/{total}")
        
        logger.info(f"✅ Traitement terminé: {processed} posts traités")
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement background: {e}")

@app.get("/get-posts")
async def get_posts(limit: int = 100):
    """Récupère les posts de la base"""
    try:
        posts = db_manager.get_posts(limit)
        return {
            "count": len(posts),
            "posts": posts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération: {str(e)}")

@app.get("/get-analysis")
async def get_analysis(limit: int = 100):
    """Récupère les analyses de toxicité"""
    try:
        analyses = db_manager.get_analysis(limit)
        return {
            "count": len(analyses),
            "analyses": analyses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Statistiques globales"""
    try:
        # Compter les posts
        total_posts = db_manager.posts_collection.count_documents({})
        
        # Compter les analyses
        total_analyses = db_manager.analysis_collection.count_documents({})
        
        # Statistiques de toxicité
        toxic_posts = db_manager.analysis_collection.count_documents({"is_toxic": True})
        
        # Moyennes des scores
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_toxicity": {"$avg": "$toxicity"},
                    "avg_threat": {"$avg": "$threat"},
                    "avg_insult": {"$avg": "$insult"}
                }
            }
        ]
        
        avg_results = list(db_manager.analysis_collection.aggregate(pipeline))
        averages = avg_results[0] if avg_results else {}
        
        return {
            "total_posts": total_posts,
            "total_analyses": total_analyses,
            "toxic_posts": toxic_posts,
            "toxicity_rate": round((toxic_posts / total_analyses * 100), 2) if total_analyses > 0 else 0,
            "average_scores": {
                "toxicity": round(averages.get("avg_toxicity", 0), 3),
                "threat": round(averages.get("avg_threat", 0), 3),
                "insult": round(averages.get("avg_insult", 0), 3)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)