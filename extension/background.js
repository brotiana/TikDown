chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "downloadVideo") {
        sendResponse({status: "processing"});
    }
});