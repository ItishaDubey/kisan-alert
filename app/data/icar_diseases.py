"""Reference knowledge base of common Indian crop diseases/pests, based on
publicly documented ICAR (Indian Council of Agricultural Research) and state
agricultural university advisories. Used to seed the RAG index in
scripts/seed_rag.py — this is not exhaustive, just enough breadth across
major crops to demonstrate retrieval-augmented diagnosis.
"""

DISEASES = [
    {
        "id": "wheat_rust",
        "crop": "wheat",
        "name": "Wheat Rust (Yellow/Brown/Black Rust)",
        "symptoms": "Yellow, orange, or brown powdery pustules on leaves and stems, arranged in stripes (yellow rust) or scattered (brown/black rust). Leaves may dry and wither in severe cases.",
        "cause": "Fungal infection (Puccinia species), favored by cool humid weather and dense sowing.",
        "remedy": "Spray a triazole-group fungicide (e.g. propiconazole) at first sign of pustules; repeat after 15 days if humid weather persists. Use rust-resistant wheat varieties in future sowing.",
    },
    {
        "id": "rice_blast",
        "crop": "rice",
        "name": "Rice Blast",
        "symptoms": "Diamond-shaped grey-centered lesions with brown margins on leaves; neck and node blast causes the panicle to break and turn white/empty.",
        "cause": "Fungal infection (Magnaporthe oryzae), spreads fast in high humidity with high nitrogen application.",
        "remedy": "Apply a tricyclazole-based fungicide at early tillering and again at boot-leaf stage. Avoid excess nitrogen fertilizer; use certified disease-free seed.",
    },
    {
        "id": "cotton_bollworm",
        "crop": "cotton",
        "name": "Cotton Bollworm (Pink/American Bollworm)",
        "symptoms": "Small holes in bolls and squares, larvae visible inside damaged bolls, premature boll shedding.",
        "cause": "Larvae of Helicoverpa armigera (American) or Pectinophora gossypiella (pink bollworm) feeding inside bolls.",
        "remedy": "Install pheromone traps to monitor moth activity. Spray a recommended insecticide (e.g. emamectin benzoate) if trap catches exceed threshold. Remove and destroy damaged bolls.",
    },
    {
        "id": "tomato_leaf_curl",
        "crop": "tomato",
        "name": "Tomato Leaf Curl Virus",
        "symptoms": "Upward curling and crinkling of leaves, yellowing along veins, stunted plant growth, reduced fruit set.",
        "cause": "Viral infection transmitted by whitefly (Bemisia tabaci); no direct chemical cure once infected.",
        "remedy": "Control whitefly vector with yellow sticky traps and a recommended insecticide (e.g. imidacloprid). Remove and destroy infected plants promptly. Use virus-resistant tomato varieties for future planting.",
    },
    {
        "id": "sugarcane_red_rot",
        "crop": "sugarcane",
        "name": "Sugarcane Red Rot",
        "symptoms": "Reddish discoloration inside the stalk with white patches (visible when cut), drying of leaves from top downward, alcohol-like smell from infected cane.",
        "cause": "Fungal infection (Colletotrichum falcatum), spreads through infected seed cane and waterlogged soil.",
        "remedy": "Use disease-free certified seed cane treated with a fungicide dip before planting. Remove and burn infected clumps. Avoid waterlogging and rotate with non-host crops like paddy or legumes.",
    },
    {
        "id": "maize_fall_armyworm",
        "crop": "maize",
        "name": "Fall Armyworm",
        "symptoms": "Ragged, elongated holes in leaves, sawdust-like frass in the whorl, damaged growing point in young plants.",
        "cause": "Larvae of Spodoptera frugiperda feeding on leaves and the central whorl.",
        "remedy": "Scout fields regularly, especially the whorl. Apply a recommended insecticide (e.g. emamectin benzoate or spinetoram) directly into the whorl in early morning or evening for best effect.",
    },
    {
        "id": "potato_late_blight",
        "crop": "potato",
        "name": "Potato Late Blight",
        "symptoms": "Water-soaked dark lesions on leaves with white fungal growth on the underside in humid conditions, rapid blackening and collapse of foliage, tuber rot in storage.",
        "cause": "Oomycete infection (Phytophthora infestans), spreads rapidly in cool, wet, humid weather.",
        "remedy": "Spray a protectant fungicide (e.g. mancozeb) preventively before disease onset, switching to a systemic fungicide (e.g. metalaxyl) once infection appears. Ensure good field drainage and avoid overhead irrigation.",
    },
    {
        "id": "chili_thrips",
        "crop": "chili",
        "name": "Chili Thrips (Leaf Curl Complex)",
        "symptoms": "Upward curling of leaves, silvery streaks on leaf undersides, stunted growth, reduced flowering.",
        "cause": "Thrips (Scirtothrix dorsalis) feeding on the underside of young leaves, often combined with viral transmission.",
        "remedy": "Use blue sticky traps to monitor thrips population. Spray a recommended insecticide (e.g. fipronil or spinosad) targeting the leaf underside. Remove severely curled leaves.",
    },
    {
        "id": "groundnut_leaf_spot",
        "crop": "groundnut",
        "name": "Groundnut Tikka Leaf Spot",
        "symptoms": "Small circular brown to black spots on leaves with a yellow halo, premature defoliation in severe cases.",
        "cause": "Fungal infection (Cercospora species), favored by warm humid weather.",
        "remedy": "Spray a chlorothalonil or mancozeb-based fungicide at first appearance of spots, repeating every 10-15 days as needed. Practice crop rotation with cereals.",
    },
    {
        "id": "onion_purple_blotch",
        "crop": "onion",
        "name": "Onion Purple Blotch",
        "symptoms": "Small white sunken spots on leaves that enlarge into purple-brown blotches with concentric rings, leaf tip dieback.",
        "cause": "Fungal infection (Alternaria porri), spreads in warm humid conditions especially after rain.",
        "remedy": "Spray a mancozeb or chlorothalonil-based fungicide at 10-day intervals during humid weather. Avoid excess nitrogen and ensure proper field drainage.",
    },
]
