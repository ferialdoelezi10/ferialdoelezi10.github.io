function showContent(sectionId) {
    console.log("Tentativo di mostrare la sezione con ID:", sectionId);
    var contents = document.getElementsByClassName('content');
    for (var i = 0; i < contents.length; i++) {
        contents[i].style.display = 'none';
    }

    var selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.style.display = 'block';
        console.log("Sezione trovata:", selectedSection);
    } else {
        console.error("Sezione con ID '" + sectionId + "' non trovata.");
    }
}

function toggleSubcategories(subcategoryId) {
    var subcategories = document.getElementById(subcategoryId);
    if (subcategories.style.display === 'block') {
        subcategories.style.display = 'none';
    } else {
        subcategories.style.display = 'block';
    }
}
document.getElementById('sidebar').addEventListener('wheel', function(event) {
    // Normalize the scroll delta for cross-browser consistency
    const delta = Math.sign(event.deltaY);

    // Adjust the scroll amount as needed
    const scrollAmount = 30; // Adjust the value to make the scrolling smoother or faster

    // Scroll the sidebar element
    this.scrollBy(0, delta * scrollAmount);

    // Prevent the default action (scrolling the whole page)
    event.preventDefault();
});