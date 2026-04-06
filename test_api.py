"""
Example test script for Office Assist API endpoints.
Run this after starting the server to verify endpoints are working.
"""
import requests
import os

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    

def test_classify(pdf_path: str):
    """Test resume classification endpoint"""
    print("Testing resume classification...")
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}\n")
        return
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('resume.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/classify", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_chat(user_input: str):
    """Test chat endpoint"""
    print("Testing chat endpoint...")
    
    data = {
        "user_input": user_input
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_submit_task_text(task_text: str):
    """Test task submission with text"""
    print("Testing task submission (text)...")
    
    data = {
        "task_text": task_text
    }
    
    response = requests.post(f"{BASE_URL}/submit-task", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_submit_task_file(file_path: str):
    """Test task submission with file"""
    print("Testing task submission (file)...")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}\n")
        return
    
    with open(file_path, 'rb') as f:
        files = {'file': ('submission.txt', f, 'text/plain')}
        response = requests.post(f"{BASE_URL}/submit-task", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Office Assist API Test Suite")
    print("=" * 60 + "\n")
    
    # Test health check
    test_health_check()
    
    # Test chat
    test_chat("What is the company vacation policy?")
    
    # Test task submission with text
    task_example = """
    # Solution: Binary Search Implementation
    
    def binary_search(arr, target):
        left, right = 0, len(arr) - 1
        
        while left <= right:
            mid = (left + right) // 2
            
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1
    
    # Time Complexity: O(log n)
    # Space Complexity: O(1)
    """
    test_submit_task_text(task_example)
    
    # Uncomment to test with actual files:
    # test_classify("path/to/resume.pdf")
    # test_submit_task_file("path/to/submission.txt")
    
    print("=" * 60)
    print("Test suite complete!")
    print("=" * 60)
