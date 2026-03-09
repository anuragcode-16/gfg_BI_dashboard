// src/components/WelcomeHero.jsx

export default function WelcomeHero() {
    return (
        <div className="welcome-container">
            <div className="welcome-sparkle">AI-Powered Analytics</div>

            <h1 className="welcome-title">
                <span className="welcome-title-gradient">
                    Turn Questions into Insights, Instantly.
                </span>
            </h1>

            <p className="welcome-subtitle">
                Ask questions in plain English and get precise SQL queries, interactive
                visualizations, and actionable business insights — powered by AI.
            </p>

            <div className="welcome-cards">
                <div className="welcome-card">
                    <h3 className="welcome-card-title">Automated Synthesis</h3>
                    <p className="welcome-card-desc">
                        Natural language processing translates unstructured requests into precise SQL execution plans dynamically.
                    </p>
                </div>

                <div className="welcome-card">
                    <h3 className="welcome-card-title">Visual Intelligence</h3>
                    <p className="welcome-card-desc">
                        Algorithmic determination of optimal chart types tailored precisely to the returned data structure.
                    </p>
                </div>

                <div className="welcome-card">
                    <h3 className="welcome-card-title">Continuous Context</h3>
                    <p className="welcome-card-desc">
                        Stateful session memory enables iterative drill-downs and multi-step analytical workflows.
                    </p>
                </div>
            </div>
        </div>
    );
}
