"""
Script de prueba para el Chatbot API
Ejecutar: python test_api.py
"""

import requests
import json

# ⚠️ CAMBIA ESTA IP POR LA IP DEL SERVIDOR
API_BASE_URL = "http://192.168.1.100:8000"

def test_health():
    """Verifica que el servidor esté corriendo"""
    print("🔍 Test 1: Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✅ Servidor funcionando\n")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def test_search_articles():
    """Prueba búsqueda de artículos"""
    print("🔍 Test 2: Búsqueda de Artículos")
    data = {
        "user_input": "Necesito artículos sobre inteligencia artificial en medicina",
        "user_id": "test_user"
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Action: {result.get('action')}")
        print(f"   Keywords: {result.get('keywords')}")
        print("   ✅ Test exitoso\n")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def test_explain_concept():
    """Prueba explicación de conceptos"""
    print("🔍 Test 3: Explicar Concepto")
    data = {
        "user_input": "Explícame qué es deep learning",
        "user_id": "test_user"
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Action: {result.get('action')}")
        print(f"   Message: {result.get('message')[:100]}...")
        print("   ✅ Test exitoso\n")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def test_recommend_themes():
    """Prueba recomendación de temas"""
    print("🔍 Test 4: Recomendar Temas")
    data = {
        "user_input": "Dame temas relacionados con machine learning",
        "user_id": "test_user"
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Action: {result.get('action')}")
        print(f"   Keywords: {result.get('keywords')}")
        print("   ✅ Test exitoso\n")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False

def main():
    print("="*60)
    print("🤖 CHATBOT API - TESTS")
    print("="*60)
    print(f"URL Base: {API_BASE_URL}\n")
    
    results = []
    
    # Ejecutar tests
    results.append(("Health Check", test_health()))
    results.append(("Búsqueda de Artículos", test_search_articles()))
    results.append(("Explicar Concepto", test_explain_concept()))
    results.append(("Recomendar Temas", test_recommend_themes()))
    
    # Resumen
    print("="*60)
    print("📊 RESUMEN")
    print("="*60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests pasados")
    print("="*60)

if __name__ == "__main__":
    main()
