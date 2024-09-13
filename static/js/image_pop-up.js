// Get the modal
var modal = document.getElementById('imageModal');

// Get the image and insert it inside the modal
var img = document.getElementById('food-pyramid-image');
var modalImg = document.getElementById('modal-image');

img.onclick = function() {
    modal.style.display = "block";
    modalImg.src = this.src;
}

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal content, close the modal
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}