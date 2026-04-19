const projectsData = [
  {
    id: 1,
    title: "EGI Investment Engine",
    description: "Developed a quantitative stock analysis system evaluating true efficiency (Gain/Loss ratio). Includes automated backtesting against S&P 500 and a full local Web Dashboard.",
    tags: ["Python", "Pandas", "Vanilla JS", "Data Analysis"],
    image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1000&auto=format&fit=crop",
    link: "#"
  },
  {
    id: 2,
    title: "Bitcoin Universal Quant v4",
    description: "Engineered an overfitting-free cryptocurrency trading bot. Uses EMA trend and pure ATR trailing stops, successfully outperforming Buy & Hold in bear markets across 12 different coins.",
    tags: ["Trading Algorithm", "Python", "yfinance", "TA"],
    image: "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1000&auto=format&fit=crop",
    link: "#"
  },
  {
    id: 3,
    title: "3D Hand Tracking Combat",
    description: "A first-person 3D arena game where users cast magical spells using real-world hand gestures. Implemented a shape-recognition engine translating drawings into game mechanics.",
    tags: ["3D Graphics", "Computer Vision", "Game Dev", "C#"],
    image: "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1000&auto=format&fit=crop",
    link: "#"
  },
  {
    id: 4,
    title: "3D Platformer Boss Fight",
    description: "Designed a challenging custom boss battle with dynamic attack telegraphs (shockwaves, lasers). Fixed physics collision bugs and enhanced castle environment fidelity.",
    tags: ["Game Engine", "Level Design", "AI Behavior"],
    image: "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop",
    link: "#"
  }
];

// Initialize Portfolio
document.addEventListener("DOMContentLoaded", () => {
  const projectsGrid = document.getElementById("projectsGrid");

  // Render Projects
  projectsData.forEach((project, index) => {
    const card = document.createElement("div");
    card.className = "card";
    // Staggered animation delay
    card.style.animation = `fadeUp 0.8s ease-out ${index * 0.2}s forwards`;
    card.style.opacity = "0"; // initial state before animation

    const tagsHtml = project.tags.map(tag => `<span class="tag">${tag}</span>`).join("");

    card.innerHTML = `
      <div class="card-image-wrap">
        <img src="${project.image}" alt="${project.title}" class="card-image" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80'">
        <div class="card-overlay"></div>
      </div>
      <div class="card-content">
        <div class="card-tags">
          ${tagsHtml}
        </div>
        <h3 class="card-title">${project.title}</h3>
        <p class="card-desc">${project.description}</p>
        <div class="card-footer">
          <a href="${project.link}" class="repo-link">View Details &rarr;</a>
        </div>
      </div>
    `;

    projectsGrid.appendChild(card);
  });

  // Dynamic Mouse Tracking on Background Grid
  const bgMatrix = document.getElementById('bgMatrix');
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    
    // Shift background gradient slightly towards mouse to create depth
    bgMatrix.style.background = `
      radial-gradient(circle at ${x * 100}% ${y * 100}%, rgba(59, 130, 246, 0.15), transparent 40%),
      radial-gradient(circle at ${(1-x) * 100}% ${(1-y) * 100}%, rgba(139, 92, 246, 0.15), transparent 40%)
    `;
  });
});
