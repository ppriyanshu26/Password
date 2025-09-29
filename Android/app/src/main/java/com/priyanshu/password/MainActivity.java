package com.priyanshu.password;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private static final String PREFS_NAME = "AppPrefs";
    private static final String KEY_PIN_SET = "pin_set";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button lockButton = findViewById(R.id.btn_lock);
        Button editButton = findViewById(R.id.btn_edit);
        Button resetButton = findViewById(R.id.btn_reset);

        lockButton.setOnClickListener(v -> lockApp());
        editButton.setOnClickListener(v -> editCards());
        resetButton.setOnClickListener(v -> resetPin());
    }

    private void lockApp() {
        Intent intent = new Intent(this, Lockscreen.class);
        startActivity(intent);
        finish();
    }

    private void editCards() {
        Toast.makeText(this, "Card management coming soon!", Toast.LENGTH_SHORT).show();
    }

    private void resetPin() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        prefs.edit()
                .remove("pin_hash")
                .putBoolean("pin_set", false)
                .apply();

        Toast.makeText(this, "PIN reset successfully!", Toast.LENGTH_SHORT).show();
        lockApp();
    }
}