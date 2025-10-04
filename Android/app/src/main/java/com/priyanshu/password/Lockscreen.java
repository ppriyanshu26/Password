package com.priyanshu.password;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class Lockscreen extends AppCompatActivity {
    private static final String PREFS_NAME = "AppPrefs";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PIN_SET = "pin_set";
    private static final String STATE_IS_SETTING_PIN = "is_setting_pin";
    private static final String STATE_PIN_TO_CONFIRM = "pin_to_confirm";

    private EditText pinInput;
    private TextView instructionText;
    private Button submitButton;
    private SharedPreferences prefs;
    private String pinToConfirm;
    private boolean isSettingPin = false;

    // Called when the activity is created
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
            isSettingPin = true;
            instructionText.setText("Create a new PIN (4-8 digits)");
            submitButton.setText("Submit");
        } else {
            instructionText.setText("Enter your PIN");
            submitButton.setText("Unlock");
        }

        pinInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                int length = s.length();
                submitButton.setEnabled(length >= 4 && length <= 8);
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });

        submitButton.setOnClickListener(v -> {
            String inputPin = pinInput.getText().toString();
            if (inputPin.length() < 4 || inputPin.length() > 8) {
                Toast.makeText(this, "PIN must be 4–8 digits", Toast.LENGTH_SHORT).show();
                return;
            }

            if (isSettingPin) {
                if (pinToConfirm == null) {
                    pinToConfirm = inputPin;
                    pinInput.setText("");
                    instructionText.setText("Confirm your PIN");
                    submitButton.setEnabled(false);
                } else {
                    if (pinToConfirm != null && inputPin.equals(pinToConfirm)) {
                        savePinHash(pinToConfirm);
                        Toast.makeText(this, "PIN set successfully!", Toast.LENGTH_SHORT).show();
                        startMainActivity();
                    } else {
                        Toast.makeText(this, "PINs don't match. Try again.", Toast.LENGTH_SHORT).show();
                        resetPinSetup();
                    }
                }
            } else {
                verifyPin();
            }
        });
    }

    // Resets the PIN setup process
    private void resetPinSetup() {
        pinToConfirm = null;
        pinInput.setText("");
        instructionText.setText("Create a new PIN (4-8 digits)");
        submitButton.setEnabled(false);
    }

    // Saves the current state of the activity
    @Override
    protected void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putBoolean(STATE_IS_SETTING_PIN, isSettingPin);
        outState.putString(STATE_PIN_TO_CONFIRM, pinToConfirm);
    }

    // Restores the previous state of the activity
    @Override
    protected void onRestoreInstanceState(@NonNull Bundle savedInstanceState) {
        super.onRestoreInstanceState(savedInstanceState);
        isSettingPin = savedInstanceState.getBoolean(STATE_IS_SETTING_PIN, false);
        pinToConfirm = savedInstanceState.getString(STATE_PIN_TO_CONFIRM);

        if (isSettingPin) {
            if (pinToConfirm == null) {
                instructionText.setText("Create a new PIN (4-8 digits)");
                submitButton.setText("Submit");
            } else {
                instructionText.setText("Confirm your PIN");
                submitButton.setText("Submit");
                submitButton.setEnabled(false);
            }
        }
    }

    // Verifies the entered PIN against the stored hash
    private void verifyPin() {
        String inputPin = pinInput.getText().toString();
        String storedHash = prefs.getString(KEY_PIN_HASH, "");
        if (hashPin(inputPin).equals(storedHash)) {
            startMainActivity();
        } else {
            Toast.makeText(this, "Incorrect PIN", Toast.LENGTH_SHORT).show();
            pinInput.setText("");
            submitButton.setEnabled(false);
        }
    }

    // Saves the hashed PIN in SharedPreferences
    private void savePinHash(String pin) {
        String hash = hashPin(pin);
        prefs.edit()
                .putString(KEY_PIN_HASH, hash)
                .putBoolean(KEY_PIN_SET, true)
                .apply();
    }

    // Hashes the PIN using SHA-256
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

    // Starts the main activity after successful unlock
    private void startMainActivity() {
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
        finish();
    }
}
