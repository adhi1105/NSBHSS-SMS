const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcodeTerminal = require('qrcode-terminal');
const qrcodeImage = require('qrcode');
const express = require('express');

const app = express();
app.use(express.json());

const port = 3000;

// Initialize WhatsApp Client with Local Session Caching
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true, // Run without popping up an actual Chrome window
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--disable-gpu',
            '--remote-debugging-port=9222',
            '--disable-extensions'
        ]
    }
});

let isReady = false;
let pairingCode = null;

// Generate QR Code for initial authentication
client.on('qr', (qr) => {
    console.log('\n[INFO] WhatsApp is waiting for authentication.');
    console.log('[TIP] You can now request a "Pairing Code" via the portal to link without a camera.');
});

// Confirm Authentication
client.on('ready', () => {
    isReady = true;
    const info = client.info;
    console.log('\n======================================================');
    console.log('✅ WHATSAPP API IS CONNECTED AND READY TO SEND MESSAGES');
    console.log(`📱 Connected as: ${info.wid.user} (${info.pushname})`);
    console.log('======================================================\n');
});

client.on('authenticated', () => {
    console.log('✅ Authentication Successful!');
});

client.on('auth_failure', msg => {
    console.error('❌ Authentication Failed:', msg);
});

client.on('disconnected', (reason) => {
    isReady = false;
    console.log('❌ WhatsApp was disconnected:', reason);
});

// Express API Route to request a Linking Pairing Code (Alternative to QR)
app.post('/api/link', async (req, res) => {
    const { phone } = req.body;
    if (!phone) return res.status(400).json({ error: 'Phone number is required.' });

    try {
        const cleanPhone = phone.replace(/\D/g, '');
        console.log(`\n🔗 Pairing Request for: ${cleanPhone}. Initializing WhatsApp Web...`);

        // Manual Injection to bypass library bug
        const code = await client.pupPage.evaluate(async (phoneNumber) => {
            // Wait for WhatsApp to be ready
            let retries = 0;
            while ((!window.AuthStore || !window.AuthStore.PairingCodeLinkUtils) && retries < 40) {
                await new Promise(resolve => setTimeout(resolve, 500));
                retries++;
            }

            if (!window.AuthStore || !window.AuthStore.PairingCodeLinkUtils) {
                throw new Error('WhatsApp Web is still loading or pairing utils are not available.');
            }

            // Trigger Alt Device Linking (Pairing Code)
            window.AuthStore.PairingCodeLinkUtils.setPairingType('ALT_DEVICE_LINKING');
            await window.AuthStore.PairingCodeLinkUtils.initializeAltDeviceLinking();
            return window.AuthStore.PairingCodeLinkUtils.startAltLinkingFlow(phoneNumber, true);
        }, cleanPhone);

        pairingCode = code;

        console.log(`\n******************************************************`);
        console.log(`🔑 YOUR WHATSAPP PAIRING CODE IS: ${code}`);
        console.log(`******************************************************\n`);

        return res.status(200).json({ success: true, pairing_code: code });
    } catch (error) {
        console.error('❌ Failed to generate pairing code:', error);

        // Check if it's the "detached frame" error specifically
        if (error.toString().includes('detached Frame')) {
            return res.status(500).json({
                error: 'WhatsApp is still starting up.',
                details: 'The browser is busy. Please wait 10 seconds and try clicking "GET CODE" again.'
            });
        }

        return res.status(500).json({ error: 'Failed to generate code', details: error.toString() });
    }
});

// Express API Route for Django to call
app.post('/api/send', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'WhatsApp Client is not ready or not authenticated yet. Please Link your phone first.' });
    }

    const { phone, message } = req.body;

    if (!phone || !message) {
        return res.status(400).json({ error: 'Phone number and message text are required.' });
    }

    try {
        const cleanPhone = phone.replace(/\D/g, '');
        const formattedNumber = `${cleanPhone}@c.us`;

        console.log(`\n📤 Attempting to send message to: ${formattedNumber}`);

        // OPTIONAL: Check if number exists on WA before sending
        try {
            const isRegistered = await client.isRegisteredUser(formattedNumber);
            if (!isRegistered) {
                console.warn(`⚠️ Warning: ${cleanPhone} does not appear to be a registered WhatsApp user.`);
            } else {
                console.log(`✅ ${cleanPhone} is a registered WhatsApp user.`);
            }
        } catch (checkErr) {
            console.error(`❌ Registration check failed: ${checkErr.message}`);
        }

        // Dispatch the message
        const response = await client.sendMessage(formattedNumber, message);

        console.log(`✉️ MESSAGE DISPATCHED TO BROWSWER.`);
        console.log(`   - To: ${cleanPhone}`);
        console.log(`   - ID: ${response.id._serialized}`);
        console.log(`   - Status: ${response.ack || 'Sent to browser'}`);

        return res.status(200).json({ success: true, response });

    } catch (error) {
        console.error(`❌ CRITICAL FAILURE sending message to ${phone}:`, error);
        return res.status(500).json({ error: 'Failed to send message', details: error.toString() });
    }
});

// Start the Express API Server
app.listen(port, () => {
    console.log(`\n🚀 Custom WhatsApp API Server running on http://localhost:${port}`);
    console.log(`⏳ Starting Headless Browser (this takes a few seconds)...`);
});

// Boot the underlying Puppeteer Engine
client.initialize();
