def detect_duplicate_emails(email_list):
    """Detects duplicate emails using TF-IDF and cosine similarity."""
    if len(email_list) < 2:
        return

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(email_list)
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    duplicates =""
    for i in range(len(email_list)):
        for j in range(i + 1, len(email_list)):
            if cosine_sim_matrix[i][j] > 0.8:  # Adjust threshold as needed
                duplicates.append((i, j, "High text similarity"))
    return duplicates