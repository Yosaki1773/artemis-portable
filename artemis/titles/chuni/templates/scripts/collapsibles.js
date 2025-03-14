///
/// Handles the collapsible behavior of each of the scrollable containers
///
/// @note Intent is to include this file via jinja in the same <script> tag as
///       any page-specific logic that interacts with the collapisbles.
///
class Collapsibles {
    static setHeight(content) {
        // @note Add an extra 20% height buffer - the div will autosize but we 
        // want to make sure we dont clip due to the horizontal scroll.
        content.style.maxHeight = (content.scrollHeight * 1.2) + "px";
    }

    static updateAllHeights() {
        // Updates the height of all expanded collapsibles. 
        // Intended for use when resolution changes cause the contents within the collapsible to move around.
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {
            var content = coll[i].nextElementSibling;
            if (content.style.maxHeight) {
                // currently visible. update height
                Collapsibles.setHeight(content);
            }
        }
    }

    static expandFirst() {
        // Activate the first collapsible once loaded so the user can get an idea of how things work
        window.addEventListener('load', function () {
            var coll = document.getElementsByClassName("collapsible");
            if (coll && coll.length > 0) {
                coll[0].click();
            }
        })
    }

    static expandAll() {
        // Activate all collapsibles so everything is visible immediately
        window.addEventListener('load', function () {
            var coll = document.getElementsByClassName("collapsible");
            for (var i = 0; i < coll.length; i++) {
                coll[i].click();
            }
        })
    }
}

//
// Initial Collapsible Setup
//

// Add an event listener for a click on any collapsible object. This will change the style to collapse/expand the content.
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
        this.classList.toggle("collapsible-active");
        var content = this.nextElementSibling;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
            content.style.opacity = 0;
        } else {
            Collapsibles.setHeight(content);
            content.style.opacity = 1;
        }
    });
}