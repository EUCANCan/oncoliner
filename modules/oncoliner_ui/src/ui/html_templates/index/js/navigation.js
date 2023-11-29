
function hideElementById(elementId) {
	document.querySelector('#' + elementId).style.display = 'none';
}

function showTabById(tabContentId) {
	var tabContent = document.querySelector('#' + tabContentId);
	showTab(tabContent);
}

function showTab(tabContent) {
	tabContent.classList.add("active","show");
}

function hideTab(tabContent) {
	tabContent.classList.remove("active","show");
}

function toggleTab(tabContentId) {
	var tabContent = document.querySelector('#' + tabContentId);

	tabContent.classList.toggle("active");
	tabContent.classList.toggle("show");
}

function toggleTabFromGroup(tabContentId, parentTabContentId) {
	var parentContent = document.querySelector('#' + parentTabContentId);

	var _children = parentContent.querySelectorAll('.tab-pane');
	for (var i = 0; i  < _children.length; i++) {
		var current = _children[i];
		hideTab(current);
	}

	showTabById(tabContentId);
}

function changeAttributeValue(id, attributeName, attributeValue) {
	var element = document.querySelector('#' + id);
	if (element) {
		element[attributeName] = attributeValue;
	}
}

function hideMenuAndUpdateSelected(element, dataContext, menuId, selectedId) {
	hideTab(document.querySelector('#' + menuId));
	changeAttributeValue(selectedId, 'innerText', dataContext);
}
