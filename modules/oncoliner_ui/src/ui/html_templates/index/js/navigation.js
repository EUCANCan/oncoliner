
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

function hideTabById(tabContentId) {
	var tabContent = document.querySelector('#' + tabContentId);
	hideTab(tabContent);
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

function removeClassOfChildren(parentId, selector, classToRemove) {
	var parentContent = document.querySelector('#' + parentId);

	var _children = parentContent.querySelectorAll(selector);

	for (var i = 0; i  < _children.length; i++) {
		var current = _children[i];
		current.classList.remove(classToRemove);
	}
}

function formatTemplate(template, array) {
	var output = template;

	array.forEach(function(val, index) {
		output = output.replace(`\{${index}\}`, val);
	});

	return output;
}

function formatTemplateFromMatrix(template, matrix) {
	var output = "";

	matrix.forEach(function(array) {
		output = output + formatTemplate(template, array);
	});

	return output;
}

function changeAttributeValue(id, attributeName, attributeValue) {
	var element = document.querySelector('#' + id);
	if (element && element[attributeName]) {
		element[attributeName] = attributeValue;
	}
}
