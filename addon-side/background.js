// globals
var timeout = null;

function sendMessage(msg) {
    console.log('postMessage("' + msg + '")');
    browser.runtime.sendNativeMessage('launcher_api_firefox_stdin.py', msg).then((response) => {
        console.log('postMessage response: ' + response);
    }, (error) => {
        console.log('postMessage error: ' + error);
    });
}

// get in_progress downloads
function updateStatus() {

    clearTimeout(timeout);

    browser.downloads.search({ state: 'in_progress' }).then((downloads) => {

        // iterate over in_progress downloads and get overall progress
        var totalBytesSum = 0;
        var bytesReceivedSum = 0;
        var progress = 0.001; // default progress
        downloads.forEach((download) => {
            if (download.totalBytes === -1) {
                return;
            }
            totalBytesSum += download.totalBytes;
            bytesReceivedSum += download.bytesReceived;
        });
        if (totalBytesSum > 0) {
            progress = bytesReceivedSum / totalBytesSum;
        }
        var count = downloads.length;

        // send count to native app
        sendMessage("count=" + count);

        // no downloads? exit.
        if (count === 0) {
            return;
        }

        // send progress to native app
        sendMessage("progress=" + progress);

        // schedule next check on status
        timeout = setTimeout(updateStatus, 1000);

    }, (error) => {

        // handle error
        console.log(`Error: ${error}`);
    });
}

// listen to download created and changed events
browser.downloads.onCreated.addListener(updateStatus);
browser.downloads.onChanged.addListener(updateStatus);

// initial call
updateStatus();
