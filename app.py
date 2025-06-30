import tweepy
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterHarassmentCollector:
    """Collecteur simple pour les posts Twitter avec #harcèlement"""
    
    def __init__(self):
        # Récupérer le token depuis les variables d'environnement
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN non trouvé dans les variables d'environnement")
        
        # Initialiser le client Twitter
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        logger.info("Client Twitter initialisé avec succès")
    
    def collect_posts(self, max_results: int = 100) -> List[Dict]:
        """
        Collecte les posts Twitter avec le hashtag #harcèlement
        
        Args:
            max_results: Nombre maximum de posts à collecter
            
        Returns:
            Liste des posts sous forme de dictionnaires
        """
        posts = []
        
        try:
            logger.info(f"Recherche de posts avec #harcèlement (max: {max_results})")
            
            # Recherche des tweets
            # Query: #harcèlement ou #harcelement, pas de retweets, en français
            query = "#harcèlement OR #harcelement -is:retweet lang:fr"
            
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                max_results=min(max_results, 100)  # API limite à 100 par requête
            ).flatten(limit=max_results)
            
            for tweet in tweets:
                # Créer un dictionnaire simple pour chaque post
                post_data = {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'author_id': f"user_{tweet.author_id}",  # Anonymisé
                    'created_at': tweet.created_at.isoformat(),
                    'likes': tweet.public_metrics['like_count'] if tweet.public_metrics else 0,
                    'retweets': tweet.public_metrics['retweet_count'] if tweet.public_metrics else 0,
                    'replies': tweet.public_metrics['reply_count'] if tweet.public_metrics else 0,
                    'url': f"https://twitter.com/user/status/{tweet.id}",
                    'collected_at': datetime.now().isoformat()
                }
                
                posts.append(post_data)
                
            logger.info(f"✅ {len(posts)} posts collectés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la collecte: {e}")
            
        return posts
    
    def save_to_json(self, posts: List[Dict], filename: str = "harassment_posts.json"):
        """Sauvegarder les posts en JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Données sauvegardées dans {filename}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde JSON: {e}")
    
    def save_to_csv(self, posts: List[Dict], filename: str = "harassment_posts.csv"):
        """Sauvegarder les posts en CSV"""
        if not posts:
            logger.warning("Aucun post à sauvegarder")
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=posts[0].keys())
                writer.writeheader()
                writer.writerows(posts)
            logger.info(f"✅ Données sauvegardées dans {filename}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde CSV: {e}")
    
    def print_stats(self, posts: List[Dict]):
        """Afficher des statistiques simples"""
        if not posts:
            logger.info("Aucun post à analyser")
            return
            
        total_likes = sum(post['likes'] for post in posts)
        total_retweets = sum(post['retweets'] for post in posts)
        total_replies = sum(post['replies'] for post in posts)
        
        logger.info("📊 STATISTIQUES:")
        logger.info(f"   Total posts: {len(posts)}")
        logger.info(f"   Total likes: {total_likes}")
        logger.info(f"   Total retweets: {total_retweets}")
        logger.info(f"   Total réponses: {total_replies}")
        
        # Afficher quelques exemples
        logger.info("\n📝 EXEMPLES DE POSTS:")
        for i, post in enumerate(posts[:3]):  # Afficher les 3 premiers
            text_preview = post['text'][:100] + "..." if len(post['text']) > 100 else post['text']
            logger.info(f"   {i+1}. {text_preview}")

def main():
    """Fonction principale"""
    print("🚀 Démarrage du collecteur Twitter #harcèlement")
    print("=" * 50)
    
    try:
        # Initialiser le collecteur
        collector = TwitterHarassmentCollector()
        
        # Collecter les posts
        posts = collector.collect_posts(max_results=50)  # Commencer petit
        
        if posts:
            # Sauvegarder les données
            collector.save_to_json(posts)
            collector.save_to_csv(posts)
            
            # Afficher les statistiques
            collector.print_stats(posts)
        else:
            logger.warning("⚠️ Aucun post collecté")
            
    except Exception as e:
        logger.error(f"❌ Erreur dans le programme principal: {e}")
        print("\n💡 AIDE:")
        print("1. Vérifiez que TWITTER_BEARER_TOKEN est défini dans votre fichier .env")
        print("2. Assurez-vous d'avoir accès à l'API Twitter")

if __name__ == "__main__":
    main()