package com.priyanshu.password;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class Lockscreen extends AppCompatActivity {
    private static final String PREFS_NAME = "AppPrefs";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PIN_SET = "pin_set";

    private EditText pinInput;
    private TextView instructionText;
    private Button submitButton;
    private SharedPreferences prefs;
    private String pinToConfirm;
    private boolean isSettingPin = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_lockscreen);

        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        pinInput = findViewById(R.id.pin_input);
        instructionText = findViewById(R.id.instruction_text);
        submitButton = findViewById(R.id.submit_button);

        boolean pinSet = prefs.getBoolean(KEY_PIN_SET, false);

        if (!pinSet) {
            // First-time setup
            startPinSetup();
        } else {
            // Normal unlock flow
            instructionText.setText("Enter your PIN");
            submitButton.setText("Unlock");
            submitButton.setOnClickListener(v -> verifyPin());
        }

        // Auto-submit when 4-8 digits entered
        pinInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (s.length() >= 4 && s.length() <= 8) {
                    if (isSettingPin) {
                        if (pinToConfirm == null) {
                            // First entry
                            pinToConfirm = s.toString();
                            pinInput.setText("");
                            instructionText.setText("Confirm your PIN");
                        } else {
                            if (s.toString().equals(pinToConfirm)) {
                                savePinHash(pinToConfirm);
                                Toast.makeText(getApplicationContext(), "PIN set successfully!", Toast.LENGTH_SHORT).show();
                                startMainActivity();
                            } else {
                                Toast.makeText(getApplicationContext(), "PINs don't match. Try again.", Toast.LENGTH_SHORT).show();
                                pinInput.setText("");
                                instructionText.setText("Create a new PIN (4-8 digits)");
                                pinToConfirm = null;
                            }
                        }
                    } else {
                        verifyPin();
                    }
                }
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });
    }

    private void startPinSetup() {
        isSettingPin = true;
        instructionText.setText("Create a new PIN (4-8 digits)");
        submitButton.setVisibility(View.GONE);
        pinToConfirm = null;
    }

    private void verifyPin() {
        String inputPin = pinInput.getText().toString();
        if (inputPin.length() < 4 || inputPin.length() > 8) {
            Toast.makeText(this, "PIN must be 4-8 digits", Toast.LENGTH_SHORT).show();
            return;
        }

        String storedHash = prefs.getString(KEY_PIN_HASH, "");
        if (hashPin(inputPin).equals(storedHash)) {
            startMainActivity();
        } else {
            Toast.makeText(this, "Incorrect PIN", Toast.LENGTH_SHORT).show();
            pinInput.setText("");
        }
    }

    private void savePinHash(String pin) {
        String hash = hashPin(pin);
        prefs.edit()
                .putString(KEY_PIN_HASH, hash)
                .putBoolean(KEY_PIN_SET, true)
                .apply();
    }

    private String hashPin(String pin) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(pin.getBytes());
            StringBuilder hexString = new StringBuilder();
            for (byte b : hashBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }

    private void startMainActivity() {
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
        finish();
    }
}