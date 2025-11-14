"""
Expanded Prompt Library for Fine-Tuning Data Generation

Each pattern has 15 diverse prompts to minimize duplication.
Prompts 0-14 (odd for OpenAI, even for Gemini)
"""

EXPANDED_PROMPTS = {
    "Hint-Based Learning": [
        "My API is returning 500 errors intermittently. What could be wrong?",
        "The database queries are slow. Where should I look?",
        "Memory usage keeps growing in my Node.js app. Help me debug this.",
        "My React component isn't re-rendering when state changes. What am I missing?",
        "The authentication flow breaks after deploying. What should I check?",
        "CSS layouts break on mobile devices. How do I troubleshoot this?",
        "WebSocket connections keep dropping. What should I investigate?",
        "File uploads timeout for large files. Where's the bottleneck?",
        "Redis cache isn't invalidating properly. What could be the issue?",
        "JWT tokens expire too quickly for users. How should I approach this?",
        "Search functionality returns incorrect results. Where do I start debugging?",
        "Email notifications aren't being sent. What should I verify?",
        "Payment webhooks are failing silently. How do I debug this?",
        "Image compression isn't working as expected. What am I missing?",
        "Rate limiting blocks legitimate users. How do I fix this?",
    ],
    "Diminishing Returns": [
        "Should I optimize my algorithm from O(n log n) to O(n)?",
        "Is it worth adding Redis caching to reduce response time from 50ms to 30ms?",
        "Should we migrate to Kubernetes for our 3-service application?",
        "Is it worth refactoring this 200-line function that works fine?",
        "Should I implement server-side rendering to improve SEO?",
        "Is it worth splitting our monolith into 20 microservices?",
        "Should I add GraphQL subscriptions for real-time updates?",
        "Is database sharding necessary for 10K daily active users?",
        "Should we implement event sourcing for our e-commerce app?",
        "Is it worth migrating from REST to gRPC for internal services?",
        "Should I add full-text search with Elasticsearch?",
        "Is service mesh worth it for 5 microservices?",
        "Should we implement CQRS for better read performance?",
        "Is edge caching worth the complexity for our use case?",
        "Should I parallelize this batch job that takes 2 minutes?",
    ],
    "Multi-Dimensional Evaluation": [
        "Review my plan to use GraphQL instead of REST for our API",
        "Evaluate this architecture: microservices with event sourcing",
        "Review my decision to use NoSQL instead of SQL",
        "Assess this approach: serverless functions for all backend logic",
        "Evaluate using WebAssembly for performance-critical features",
        "Review my plan to adopt TypeScript across the entire codebase",
        "Evaluate switching from monorepo to polyrepo structure",
        "Assess using WebSockets vs Server-Sent Events for real-time features",
        "Review my decision to use Docker Swarm instead of Kubernetes",
        "Evaluate adopting trunk-based development over GitFlow",
        "Assess using Firebase instead of building custom backend",
        "Review my plan to migrate from MySQL to PostgreSQL",
        "Evaluate using Redux vs Context API for state management",
        "Assess implementing micro-frontends for our dashboard",
        "Review my decision to use Next.js instead of Create React App",
    ],
    "Precision Policing": [
        "How do closures work in JavaScript?",
        "Explain async/await in Python",
        "What's the difference between TCP and UDP?",
        "How does garbage collection work?",
        "Explain the difference between authentication and authorization",
        "What's the difference between REST and RPC?",
        "How do database transactions ensure ACID properties?",
        "Explain the difference between cookies and local storage",
        "What's the CAP theorem in distributed systems?",
        "How does TLS/SSL encryption work?",
        "Explain the difference between horizontal and vertical scaling",
        "What's the difference between PUT and PATCH in HTTP?",
        "How do B-tree indexes work in databases?",
        "Explain eventual consistency vs strong consistency",
        "What's the difference between mocking and stubbing in tests?",
    ],
    "Brutal Accuracy": [
        "I think TypeScript is always better than JavaScript. Right?",
        "NoSQL is faster than SQL, so we should always use it. Agree?",
        "Microservices are superior to monoliths in every case. True?",
        "TDD guarantees bug-free code. Correct?",
        "Cloud is always cheaper than on-premise. Yes?",
        "Using the latest framework version is always the best practice. Right?",
        "More code comments make code more maintainable. True?",
        "Agile is better than Waterfall in all scenarios. Agree?",
        "100% test coverage means no bugs. Correct?",
        "Serverless is always more cost-effective. True?",
        "Docker containers are always faster than VMs. Right?",
        "GraphQL is replacing REST everywhere. Agree?",
        "Stateless architecture is always better. True?",
        "Functional programming is superior to OOP. Right?",
        "Using ORMs is always better than raw SQL. Agree?",
    ],
    "Tradeoff Analysis": [
        "Should I use React or Vue for my new project?",
        "PostgreSQL vs MySQL for an e-commerce platform?",
        "Monorepo vs polyrepo for our team of 10 developers?",
        "REST vs GraphQL for a mobile app backend?",
        "Docker Compose vs Kubernetes for development?",
        "AWS vs Google Cloud vs Azure for a startup?",
        "Redis vs Memcached for session storage?",
        "Jenkins vs GitHub Actions for CI/CD?",
        "MongoDB vs PostgreSQL for a social media app?",
        "gRPC vs REST for microservice communication?",
        "Terraform vs CloudFormation for infrastructure?",
        "Vim vs VS Code for Python development?",
        "JWT vs session cookies for authentication?",
        "WebSockets vs polling for real-time notifications?",
        "SQLite vs PostgreSQL for a mobile app backend?",
    ],
    "Gap Analysis": [
        "I'm building a payment processing system. What should I consider?",
        "Planning a real-time chat application. What am I missing?",
        "Designing a CI/CD pipeline. What gaps might I have?",
        "Creating a multi-tenant SaaS app. What should I address?",
        "Building an API rate limiter. What factors should I consider?",
        "Designing a video streaming platform. What am I overlooking?",
        "Building a file sharing service. What security concerns exist?",
        "Creating a job queue system. What edge cases should I handle?",
        "Designing an OAuth provider. What compliance issues matter?",
        "Building a search engine for our app. What should I account for?",
        "Creating a notification system. What delivery guarantees do I need?",
        "Designing a metrics collection system. What scalability issues exist?",
        "Building a content moderation pipeline. What biases should I address?",
        "Creating an API gateway. What reliability concerns should I plan for?",
        "Designing a caching strategy. What invalidation patterns should I use?",
    ],
    "Production Readiness": [
        "Write a function to handle file uploads",
        "Create an endpoint for user registration",
        "Implement a caching layer for our API",
        "Build a retry mechanism for failed API calls",
        "Write a background job processor",
        "Create a webhook receiver for payment events",
        "Implement rate limiting middleware",
        "Build an email verification system",
        "Write a database migration script",
        "Create a health check endpoint",
        "Implement request logging middleware",
        "Build a password reset flow",
        "Write a CSV export function for large datasets",
        "Create a session management system",
        "Implement API key authentication",
    ],
    "Mechanistic Understanding": [
        "Explain how HTTPS encryption works",
        "How does database indexing improve query performance?",
        "Explain how DNS resolution works",
        "How do load balancers distribute traffic?",
        "Explain how OAuth 2.0 works",
        "How does JWT token validation work?",
        "Explain how React's virtual DOM improves performance",
        "How does Redis achieve such high throughput?",
        "Explain how database replication maintains consistency",
        "How do CDNs reduce latency globally?",
        "Explain how websockets maintain persistent connections",
        "How does Docker containerization isolate processes?",
        "Explain how Git handles merge conflicts",
        "How does HTTP/2 multiplexing improve performance?",
        "Explain how Kubernetes schedules pods across nodes",
    ],
    "Context-Dependent Recommendations": [
        "What's the best database for my application?",
        "How should I deploy my web app?",
        "What testing strategy should I use?",
        "Which cloud provider should I choose?",
        "What's the best way to handle file storage?",
        "What caching strategy should I implement?",
        "How should I structure my API endpoints?",
        "What authentication method should I use?",
        "How should I handle database migrations?",
        "What logging strategy should I adopt?",
        "How should I monitor my application?",
        "What backup strategy should I implement?",
        "How should I handle error reporting?",
        "What API versioning strategy should I use?",
        "How should I secure my API?",
    ],
}


def get_prompts_for_provider(provider: str, pattern: str) -> list[str]:
    """
    Get prompts for a specific provider to ensure diversity.

    OpenAI gets odd indices (0, 2, 4, 6, 8, 10, 12, 14)
    Gemini gets even indices (1, 3, 5, 7, 9, 11, 13)

    This ensures no duplicate prompts across providers.
    """
    all_prompts = EXPANDED_PROMPTS[pattern]

    if provider.lower() == "openai":
        # Odd indices: 0, 2, 4, 6, 8, 10, 12, 14
        return [all_prompts[i] for i in range(0, len(all_prompts), 2)]
    elif provider.lower() == "gemini":
        # Even indices: 1, 3, 5, 7, 9, 11, 13
        return [all_prompts[i] for i in range(1, len(all_prompts), 2)]
    else:
        raise ValueError(f"Unknown provider: {provider}")
